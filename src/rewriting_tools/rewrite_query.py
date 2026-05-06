from pglast import parse_sql
from pglast.stream import RawStream
from pglast.ast import SelectStmt, RangeVar, SubLink, ColumnRef, A_Expr, JoinExpr, BoolExpr, ResTarget, String
from pglast.enums.nodes import JoinType
from pglast.enums import SubLinkType
from pglast.enums import BoolExprType
from pglast.enums.nodes import LimitOption
from pprint import pprint

#returns (sublink, parent, position)
def find_sublink(node_in_where_clause) :
    return find_sublink_helper(node_in_where_clause, None, None)


def find_sublink_helper(node_in_where_clause, parent, position) :
    if isinstance(node_in_where_clause, SubLink) :
        # Check if the sublink's subselect has a GROUP BY clause
        subselect = node_in_where_clause.subselect
        if hasattr(subselect, 'groupClause') and subselect.groupClause is not None:
            # This sublink has a GROUP BY clause, skip it
            pass
        else:
            # No GROUP BY clause, return this sublink
            return (node_in_where_clause, parent, position)
    elif isinstance(node_in_where_clause, BoolExpr) and node_in_where_clause.boolop.name=='AND_EXPR':
        for child_index, current_child in enumerate(node_in_where_clause.args):
            current_child_result = find_sublink_helper(current_child, node_in_where_clause, child_index)
            if current_child_result[0] != None:
                return current_child_result
    return (None, None, None)


def transform_in_subquery_to_join(statements):
    statements, modified = transform_in_subquery_to_join_helper(statements)
    while modified :
        statements, modified = transform_in_subquery_to_join_helper(statements)
    return statements

def transform_in_subquery_to_join_helper(statements):
    """
    Input: list of Statement nodes from pglast.parse_sql()
    Transforms IN-subquery to INNER JOIN in-place when not a self-join,
    but always pulls out ORDER BY and LIMIT clauses.
    """
    modified = False
    for stmt_wrapper in statements:
        stmt_node = stmt_wrapper.stmt
        if not isinstance(stmt_node, SelectStmt):
            continue

        # Must have exactly one FROM table (RangeVar)
        from_clause = stmt_node.fromClause
        if not from_clause or len(from_clause) != 1 or not (isinstance(from_clause[0], RangeVar) or isinstance(from_clause[0], JoinExpr)) :
            print('Skipping because of the from-clause:')
            print(from_clause)
            continue

        main_from_clause = from_clause[0]
        
        # Check if WHERE is a SubLink (IN subquery)
        where_clause = stmt_node.whereClause
        sublink_node, sublink_parent, sublink_position = find_sublink(where_clause)
        if not where_clause or sublink_node == None:
            print('Ignoring query because it does not contain a subquery inside a where clause')
            continue

        print('Processing the query because it has a sublink node')
            
        if sublink_node.subLinkType != SubLinkType.ANY_SUBLINK:
            continue

        testexpr = sublink_node.testexpr
        if not isinstance(testexpr, ColumnRef):
            continue

        # Preserve the full qualification for the outer column
        outer_col_ref = testexpr
        
        subselect = sublink_node.subselect
        if not isinstance(subselect, SelectStmt):
            continue

        sub_from = subselect.fromClause
        if not sub_from or len(sub_from) != 1 or not isinstance(sub_from[0], RangeVar):
            continue

        sub_table = sub_from[0]

        sub_target = subselect.targetList
        if not sub_target or len(sub_target) != 1:
            continue

        sub_col_ref = sub_target[0].val
        
        if not isinstance(sub_col_ref, ColumnRef):
            continue
        
        # Use the full inner column reference as-is
        inner_col_ref = sub_col_ref

        # Check if this would be a trivial/self join by comparing column references
        def column_refs_equal(col1, col2):
            """Check if two ColumnRef objects reference the same qualified column"""
            if len(col1.fields) != len(col2.fields):
                return False
            for f1, f2 in zip(col1.fields, col2.fields):
                if f1.sval != f2.sval:
                    return False
            return True

        is_self_join = column_refs_equal(outer_col_ref, inner_col_ref)

        # Always pull out ORDER BY and LIMIT from subquery, regardless of self-join
        if (stmt_node.sortClause == None):
            stmt_node.sortClause = subselect.sortClause

        if (stmt_node.limitOption == LimitOption.LIMIT_OPTION_DEFAULT) :
            stmt_node.limitOption = subselect.limitOption
            stmt_node.limitCount = subselect.limitCount

        # Remove the sublink from WHERE clause in both cases
        new_where_clause = None
        if sublink_parent is None:
            # Sublink is the entire WHERE clause
            new_where_clause = None
        else:
            # Sublink is part of a BoolExpr - reconstruct without the sublink
            args_list = list(sublink_parent.args)
            if len(args_list) == 2:
                # Binary AND: keep the other argument
                other_arg = args_list[1 - sublink_position]
                new_where_clause = other_arg
            elif len(args_list) > 2:
                # Multi-argument AND: remove the sublink argument
                del args_list[sublink_position]
                if len(args_list) == 1:
                    new_where_clause = args_list[0]
                else:
                    new_where_clause = BoolExpr(
                        boolop=BoolExprType.AND_EXPR,
                        args=tuple(args_list)
                    )
            else:
                new_where_clause = None

        # Only create JOIN if it's not a self-join
        if not is_self_join:
            # Build JOIN condition
            join_condition = A_Expr(
                kind=0,  # AEXPR_OP
                name=('=',),
                lexpr=outer_col_ref,
                rexpr=inner_col_ref
            )

            join_expr = JoinExpr(
                jointype=JoinType.JOIN_INNER,
                isNatural=False,
                larg=main_from_clause,
                rarg=sub_table,
                quals=join_condition
            )
            
            # Replace FROM clause with JOIN
            stmt_node.fromClause = (join_expr,)

            # Move subquery's WHERE to main query
            sub_where = subselect.whereClause
            if sub_where:
                if new_where_clause is None:
                    new_where_clause = sub_where
                else:
                    # Combine with existing WHERE clause using AND
                    new_where_clause = BoolExpr(
                        boolop=BoolExprType.AND_EXPR,
                        args=(new_where_clause, sub_where)
                    )
        else:
            print('Do not create a join because it is a self-join')

        # Apply the new WHERE clause
        stmt_node.whereClause = new_where_clause
        modified = True

    return statements, modified

def rewrite_sql(original_sql) :
    # Parse → returns list of Statement(nodes)
    parsed = parse_sql(original_sql)
    #print('Before rewriting:')
    #pprint(parsed[0].stmt(skip_none=True))
        

    # Transform
    transformed = transform_in_subquery_to_join(parsed)

    #print('After rewriting:')
    #pprint(transformed[0].stmt(skip_none=True))
    
    # Reconstruct full SQL
    select_stmt = transformed[0].stmt  # assuming single statement

    new_sql = RawStream()(select_stmt)
    return new_sql

# === Usage ===
if __name__ == "__main__":
    original_sql = """
    SELECT link_to_event 
    FROM attendance 
    WHERE link_to_member IN (
        SELECT link_to_member 
        FROM expense 
        WHERE cost > 50
    )
    """

    print(rewrite_sql(original_sql))