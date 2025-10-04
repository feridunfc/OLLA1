from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def read_root():
    return {"Hello": "World"}
```
To run the application, use Uvicorn:
```bash
uvicorn main:app --reload
```
This will start a server at http://localhost:8000/. You can see your API documentation on this URL. 

The project structure could be something like this:
```
/my_fastapi_project
     /venv (if you're using virtual environments)
    main.py
    requirements.txt
```
In `requirements.txt`, you would have the following:
```
fastapi
uvicorn
```
This is a very basic setup for a FastAPI application. You can extend it according to your needs by adding more routes and functionality. 

Remember that FastAPI is asynchronous by nature, so if you're planning on using databases or other IO-bound operations, make sure they support async operations.
