py -3.9 generate_key.py > temp_key
set /p key_1= < temp_key
del temp_key

py -3.9 generate_key.py > temp_key
set /p key_2= < temp_key
del temp_key

py -3.9 generate_key.py > temp_key
set /p key_3= < temp_key
del temp_key

py -3.9 generate_key.py > temp_key
set /p key_4= < temp_key
del temp_key

echo SEED_KEY=str(0X%key_1%-(0X%key_2%+0X%key_3%)//0X%key_4%) > seed_key.py

py -3.9 generate_key.py > build_key.txt
