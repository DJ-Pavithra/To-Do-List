from flask import Flask, render_template, request, redirect
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///todo_final.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# --- Models ---
class Todo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(200), nullable=False)
    priority = db.Column(db.String(20), default='Medium')
    category = db.Column(db.String(50), default='General')
    completed = db.Column(db.Integer, default=0)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)
    subtasks = db.relationship('SubTask', backref='parent', cascade="all, delete-orphan", lazy=True)

class SubTask(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(150), nullable=False)
    completed = db.Column(db.Integer, default=0)
    todo_id = db.Column(db.Integer, db.ForeignKey('todo.id'), nullable=False)

with app.app_context():
    db.create_all()

# --- Logic ---
@app.route('/', methods=['POST', 'GET'])
def index():
    if request.method == 'POST':
        content = request.form.get('content')
        if content:
            new_task = Todo(
                content=content, 
                priority=request.form.get('priority', 'Medium'), 
                category=request.form.get('category', 'General')
            )
            db.session.add(new_task)
            db.session.commit()
        return redirect('/')
    
    tasks = Todo.query.order_by(Todo.completed, Todo.date_created.desc()).all()
    
    # Progress Calculation: Counts tasks (if no subs) or subtasks (if they exist)
    total_units = 0
    finished_units = 0
    for t in tasks:
        if not t.subtasks:
            total_units += 1
            if t.completed == 1: finished_units += 1
        else:
            total_units += len(t.subtasks)
            finished_units += len([s for s in t.subtasks if s.completed == 1])
            
    progress = int((finished_units / total_units * 100)) if total_units > 0 else 0
    return render_template('index.html', tasks=tasks, global_progress=progress, total=total_units, finished=finished_units)

@app.route('/add_subtask/<int:todo_id>', methods=['POST'])
def add_subtask(todo_id):
    content = request.form.get('subcontent')
    if content:
        db.session.add(SubTask(content=content, todo_id=todo_id))
        db.session.commit()
    return redirect('/')

@app.route('/add_global_subtask', methods=['POST'])
def add_global_subtask():
    content = request.form.get('global_subcontent')
    selected_ids = request.form.getlist('selected_tasks')
    if content and selected_ids:
        for tid in selected_ids:
            db.session.add(SubTask(content=content, todo_id=int(tid)))
        db.session.commit()
    return redirect('/')

@app.route('/toggle_subtask/<int:id>')
def toggle_subtask(id):
    sub = SubTask.query.get_or_404(id)
    sub.completed = 1 if sub.completed == 0 else 0
    db.session.commit()
    return redirect('/')

@app.route('/update/<int:id>')
def update(id):
    t = Todo.query.get_or_404(id)
    t.completed = 1 if t.completed == 0 else 0
    db.session.commit()
    return redirect('/')

@app.route('/delete/<int:id>')
def delete(id):
    db.session.delete(Todo.query.get_or_404(id))
    db.session.commit()
    return redirect('/')

if __name__ == "__main__":
    app.run(debug=True)