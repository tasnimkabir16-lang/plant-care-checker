# Plant Care Checker

A simple Flask-based web application that provides plant care information and performs basic leaf health analysis using image color detection.

## Features

- Select a plant from a predefined list
- Upload a leaf image
- Analyze green, yellow, and brown areas of the leaf
- Display basic plant care information
- Optional plant identification using the Pl@ntNet API

## Supported Plants

- Rose
- Tomato
- Mango
- Hibiscus
- Chili Pepper
- Basil / Tulsi
- Aloe Vera
- Money Plant

## Technologies Used

- Python
- Flask
- HTML
- CSS
- Pillow
- Requests
- Pl@ntNet API

## Project Structure

`text
plant-care-checker/
├── app.py
├── requirements.txt
├── templates/
│   └── index.html
└── static/
    └── style.css
