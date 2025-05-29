from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List
import psycopg2
import psycopg2.extras

app = FastAPI()

# Serve static files
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", response_class=FileResponse)
def serve_home():
    return FileResponse("static/index.html")

# Database connection
conn = psycopg2.connect(
    host="localhost",
    port = "5432",
    database="apidb",
    user="postgres",
    password="postgres"
)

# Models
class Post(BaseModel):
    title: str
    content: str

class PostOut(Post):
    id: int

# CREATING CRUD API
@app.get("/posts", response_model=List[PostOut])
def get_posts():
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute("SELECT * FROM posts")
        return cur.fetchall()

@app.get("/posts/{post_id}", response_model=PostOut)
def get_post(post_id: int):
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute("SELECT * FROM posts WHERE id = %s", (post_id,))
        post = cur.fetchone()
        if not post:
            raise HTTPException(status_code=404, detail="Post not found")
        return post

@app.post("/posts", response_model=PostOut)
def create_post(post: Post):
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(
            "INSERT INTO posts (title, content) VALUES (%s, %s) RETURNING *",
            (post.title, post.content)
        )
        new_post = cur.fetchone()
        conn.commit()
        return new_post

@app.put("/posts/{post_id}", response_model=PostOut)
def update_post(post_id: int, post: Post):
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute("SELECT * FROM posts WHERE id = %s", (post_id,))
        if not cur.fetchone():
            raise HTTPException(status_code=404, detail="Post not found")

        cur.execute(
            "UPDATE posts SET title = %s, content = %s WHERE id = %s RETURNING *",
            (post.title, post.content, post_id)
        )
        updated_post = cur.fetchone()
        conn.commit()
        return updated_post

@app.delete("/posts/{post_id}")
def delete_post(post_id: int):
    with conn.cursor() as cur:
        cur.execute("DELETE FROM posts WHERE id = %s RETURNING id", (post_id,))
        result = cur.fetchone()
        if not result:
            raise HTTPException(status_code=404, detail="Post not found")
        conn.commit()
        return {"detail": "Post deleted"}gi