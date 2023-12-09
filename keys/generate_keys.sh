key_1=$(python generate_key.py)
key_2=$(python generate_key.py)
key_3=$(python generate_key.py)
key_4=$(python generate_key.py)

echo "SEED_KEY=str(0X$key_1-(0X$key_2+0X$key_3)*0X$key_4)" > seed_key.py
