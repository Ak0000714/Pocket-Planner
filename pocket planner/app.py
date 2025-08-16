from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3
from datetime import datetime
import numpy as np
import os

app = Flask(__name__)
app.secret_key = 'ajmal-expensetrack-key'  # required for flash(), session, etc.


DB_FILE = 'expenses_tracker.db'

def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db_connection() as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS expense (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT NOT NULL,
                amount REAL NOT NULL,
                description TEXT,
                date DATE NOT NULL
            )
        ''')
        conn.execute('''
            CREATE TABLE IF NOT EXISTS budget (
                id INTEGER PRIMARY KEY,
                budget REAL NOT NULL
            )
        ''')

@app.route('/')
def index():
    try:
        conn = get_db_connection()
        expenses = conn.execute('SELECT * FROM expense ORDER BY date DESC').fetchall()
        categories = conn.execute('SELECT DISTINCT category FROM expense').fetchall()
        category_list = [c['category'] for c in categories]
        budget_row = conn.execute('SELECT * FROM budget LIMIT 1').fetchone()
        budget = budget_row['budget'] if budget_row else 0
        total_expenses = sum([exp['amount'] for exp in expenses])
        balance = budget - total_expenses

        category_expenses = []
        for cat in category_list:
            result = conn.execute('SELECT SUM(amount) AS total FROM expense WHERE category = ?', (cat,)).fetchone()
            category_expenses.append(result['total'] if result['total'] else 0)

        monthly = {}
        for exp in expenses:
            month = datetime.strptime(exp['date'], '%Y-%m-%d').strftime('%B')
            monthly[month] = monthly.get(month, 0) + exp['amount']

        monthly_data = {
            'labels': list(monthly.keys()),
            'values': list(monthly.values())
        }

        future_prediction = np.mean(monthly_data['values']) if monthly_data['values'] else 0

        return render_template(
            'index.html',
            expenses=expenses,
            categories=category_list,
            total_expenses=total_expenses,
            balance=balance,
            budget=budget,
            category_expenses=category_expenses,
            monthly_expenses=monthly_data,
            future_expenses_prediction=future_prediction
        )
    except Exception:
        flash("Error loading page", "error")
        return redirect(url_for('index'))

@app.route('/add', methods=['POST'])
def add_expense():
    try:
        category = request.form['category']
        amount = request.form['amount']
        description = request.form.get('description', '')
        date = request.form['date']

        try:
            amount = float(amount)
            if amount <= 0:
                raise ValueError()
        except:
            flash("Invalid amount", "error")
            return redirect(url_for('index'))

        try:
            date_obj = datetime.strptime(date, '%Y-%m-%d')
        except:
            flash("Invalid date", "error")
            return redirect(url_for('index'))

        conn = get_db_connection()
        conn.execute(
            'INSERT INTO expense (category, amount, description, date) VALUES (?, ?, ?, ?)',
            (category, amount, description, date)
        )
        conn.commit()

        total_spent = conn.execute('SELECT SUM(amount) AS total FROM expense').fetchone()['total']
        budget_row = conn.execute('SELECT * FROM budget LIMIT 1').fetchone()

        if budget_row and total_spent > budget_row['budget']:
            flash(f"Warning: You have exceeded the budget by ₹{total_spent - budget_row['budget']}", "warning")
        else:
            flash("Expense added successfully!", "success")

    except Exception:
        flash("Error adding expense", "error")

    return redirect(url_for('index'))

@app.route('/delete/<int:id>')
def delete_expense(id):
    try:
        conn = get_db_connection()
        conn.execute('DELETE FROM expense WHERE id = ?', (id,))
        conn.commit()
        flash("Expense deleted", "success")
    except:
        flash("Error deleting expense", "error")
    return redirect(url_for('index'))

@app.route('/update_budget', methods=['POST'])
def update_budget():
    try:
        new_budget = request.form['budget']

        try:
            new_budget = float(new_budget)
            if new_budget < 0:
                raise ValueError()
        except:
            flash("Invalid budget value", "error")
            return redirect(url_for('index'))

        conn = get_db_connection()
        existing = conn.execute('SELECT * FROM budget LIMIT 1').fetchone()
        if existing:
            conn.execute('UPDATE budget SET budget = ? WHERE id = 1', (new_budget,))
        else:
            conn.execute('INSERT INTO budget (id, budget) VALUES (1, ?)', (new_budget,))
        conn.commit()
        flash("Budget updated successfully", "success")

    except:
        flash("Error updating budget", "error")

    return redirect(url_for('index'))

if __name__ == '__main__':
    if not os.path.exists(DB_FILE):
        init_db()
    else:
        init_db()

    app.run(debug=True)
