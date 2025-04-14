# Library Management System

This project is a simple Library Management System built using Flask (Python) for the web interface and MySQL for database management. The system allows users to borrow books, rate books, and perform CRUD operations on books and users. Librarians can manage the system, including adding, editing, and deleting users and books.

## Features

- **User Management**
  - Add, view, and delete users (users and librarians).
  
- **Book Management**
  - View, add, edit, and delete books.
  - Check the availability of books (whether they are currently borrowed or not).
  
- **Borrowing Management**
  - Borrow and return books.
  - View active borrowings (with user and book details).
  
- **Ratings**
  - Rate books after returning them.
  - View top-rated books based on average ratings.

## Requirements

- Python 3.x
- Flask
- MySQL (or compatible database)
- MySQL Connector for Python (`mysql-connector-python`)

### Install the Required Python Libraries

To install the required Python libraries, run the following command:

```bash
pip install -r requirements.txt
