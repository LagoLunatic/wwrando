py -3.8 generate_key.py > temp_seed_key
set /p seed_key= < temp_seed_key
del temp_seed_key
echo SEED_KEY="%seed_key%" > seed_key.py

py -3.8 generate_key.py > build_key.txt
