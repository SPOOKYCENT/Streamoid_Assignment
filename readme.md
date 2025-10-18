# Streamoid Product Management Backend

This project aims to provide a lightweight and user-friendly tool that helps businesses manage their product data stored in CSV or Excel files. It validates, organizes, and presents your product information, making it easier to track inventory, identify errors, and maintain consistent data.

## Features

- Upload your CSV/Excel files containing product data.
- Automatically validates your data.
  - Required fields: `sku`, `name`, `brand`, `mrp`, `price`.
  - Optional fields: `color`, `size`, `quantity`.
- See the products those had validation errors.
- Organized view of products like:
  - Paginated view.
  - Filtering by brand, color and price range.
- Potential future features like sorting and search.

## Instructions

### Step 1: Install Docker

- Download and install docker for your system: https://www.docker.com/get-started
- Make sure Docker Desktop is running before proceeding.

### Step 2: Download the project

- Clone or download the project folder to your system.

### Step 3: Build the Docker image

- Open terminal in the project folder.
- Run this command in the terminal:

  ```bash
      docker build -t [image_name]
  ```

- This creates a container image with all the required dependencies.

### Step 4: Run the server

- Start the backend using docker:

  ```bash
      docker run -p 8000:8000 [image-name]
  ```

- You can now access the backend service at http://localhost:8000

## API Reference

#### Get all products

```http
  GET /products
```

- Returns all products.

| Parameter | Type  | Description                                 |
| :-------- | :---- | :------------------------------------------ |
| `limit`   | `int` | Number of products you wish to list at once |
| `page`    | `int` | Page number                                 |

#### Filter products

```http
  GET /products/search
```

- Returns product with filters.

| Parameter  | Type     | Description                                 |
| :--------- | :------- | :------------------------------------------ |
| `brand`    | `string` | Brand name                                  |
| `color`    | `string` | Color of the product                        |
| `minPrice` | `float`  | Min price for the products                  |
| `maxPrice` | `float`  | Max price for the products                  |
| `limit`    | `int`    | Number of products you wish to list at once |
| `page`     | `int`    | Page number                                 |

#### Upload file

```http
  POST /upload
```

- Upload CSV/Excel file.
- Stores valid products to the database.
- Return failed products.

#### Clear database

```http
  POST /clear_db
```

- Clears the database.

## Benefits

- Save time: No more manually checking CSV files for error.
- Reduce mistakes: Automatic validation ensures unique SKU and correct data types.
- Organized view: Data is stored and ready for reporting.

## Future Enhancements

- Web interface for easy browsing of your product list.
- Sorting and searching.
- Export organized data back to CSV/Excel files.
