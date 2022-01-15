python generate_key.py > temp_key
key_1= < temp_key
rm temp_key

python generate_key.py > temp_key
key_2= < temp_key
rm temp_key

python generate_key.py > temp_key
key_3= < temp_key
rm temp_key

python generate_key.py > temp_key
key_4= < temp_key
rm temp_key

echo SEED_KEY=str(0X%key_1%-(0X%key_2%+0X%key_3%)*0X%key_4%) > seed_key.py

python generate_key.py 8 > build_key.txt
