# Project Prompts

All user prompts provided during the development of this FastAPI assessment project, in chronological order.

---

## 1. Initial FastAPI setup

> Setup the fastapi basic project. also add the alembic integration into that. add heath check route. manage db connection with .env file. generate the requirement.txt file

---

## 2. User authentication (JWT)

> Create User table with email and password. add the register, login , logout routes. also add the depedency injection for the db connection. once user will be the login generate the jwt token which user in other apis to get the current user

---

## 3. Category & Product CRUD

> Create the Crud operation for the category where make sure when delete category if any product attached return the erorr 409 conflict also include the product_count per category
>
> also create the product crud where the with soft delete via deleted_at. add validaton
> price>0, title between 3-200 and desrpitoin max 500
>
> make sure both table has foreign key relation and indexing on category_id, status and conposite(price,status)

---

## 4. Product listing, stock, and global errors

> Add one field in Product table with name  stock_quantity with integer and non negative.
>
> In get product listing api add the filter based on the category, min_price, max_price ,status and sorting (sort_by ,order). also add pagination with max 100 paze size.  and in resposne add the {items, total,page,page size,has_next}
>
> also add search wihic case-sensitive partially match with name and description.
>
> also add the global exception handleer with error enveliop {error:{code,message,details}}

---

## 5. Fix Alembic enum error

> fix this enum error
>
> *(Context: `sqlalchemy.exc.ProgrammingError: type "product_status" already exists` when running migrations)*

---

## 6. Docker & README

> Create docker file which run the fastapi , postgres, redis .
> Create proper readme file  and also add the sample api call

---

## 7. Environment variables

> add all credentials and key value in .env like redis url, jwt secret,

---

## 8. Database seeders

> Generate random 10 category and 50 production for that. create the seeders file to add that in db

---

## 9. Fix N+1 query on categories list

> for this remove the n+1 query
>
> *(Context: `app/api/routes/categories.py` lines 52–53 — listing categories with `product_count`)*

---

## 10. Export prompts document

> Give me one md file with all provided my prompts.

---

*Generated from the project conversation history.*
