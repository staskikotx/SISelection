# SISelection

The code for NL2SQL candidate selection based on small separating instances. To find out which on of the SQL-candidates is right we will hold duels between them.


## 🛠️ Environment Setup

1. Install necessary Python libraries:
    ```bash
    pip install -r requirements.txt
    ```
    
2. Install PostgreSQL (>=17.6) with ProvSQL extension (for creating separating instances using provenance), available at [ProvSQL Official Repository](https://github.com/PierreSenellart/provsql). 
However, initial candidate queries and databases are expected to be written using SQLite3 dialect.
    
3. There is no need to install SQLite3 directly -- just save database.sql files to some folder. Place folder with their schemas nearby. PostgreSQL, however, needs to be installed and databases uploaded, run:
    ```bash
    bash load_everything_pure.sh
    bash load_everything_prov.sh
    ```
    And execute 'add_provenance.sql' file using psql.

4. Deploy your LLM, write url and hyperparameters to src.batch_sender.send_prompt(). Once you done, you can immediately test the connection by executing:
    ```bash
    make test_remote_qwen
    ```
    Model should answer with 'Paris'.

5. Adjust 'config.py' by putting real paths to folders with candidates, databases, schemas, LLM, json with task statements, etc.


## 🚀 Ready to select

1. Now you can run:

    ```bash
    make test
    ```
    to see the algorithm in action on 3 simple examples. 

2.  Then you can run:
    ```bash
    make test_extract
    ```
    to test it on 3 examples with a lot of candidates.


 3. If everything is working fine, try choosing a range of tasks in 'run_on_bird.py' and running:
    ```bash
    make run
    ```
    That should run the algorithm on the provided subset of provided task_statements file.






