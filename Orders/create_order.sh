#!/bin/bash

# Determine the directory where the script is located (Orders/)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ORDERS_DIR="$SCRIPT_DIR"

# Check if Orders directory exists (sanity check)
if [ ! -d "$ORDERS_DIR" ]; then
  echo "Error: Directory '$ORDERS_DIR' does not exist."
  exit 1
fi

# Find the maximum number from directories matching "XXXXX_"
max_num=-1
for dir in "$ORDERS_DIR"/*; do
  if [ -d "$dir" ]; then
    dirname=$(basename "$dir")
    if [[ "$dirname" =~ ^([0-9]{5})_ ]]; then
      num=$((10#${BASH_REMATCH[1]}))
      if (( num > max_num )); then
        max_num=$num
      fi
    fi
  fi
done

# If no numbered directories found, default max_num to 0 (so next is 1), 
# checking if 00000 exists effectively sets max_num to 0 if it's the only one.
if (( max_num == -1 )); then
  max_num=0
fi

next_num=$((max_num + 1))
formatted_next_num=$(printf "%05d" "$next_num")

# Read input
echo -n "Enter name for (${formatted_next_num}_...): "
read input_name

if [ -z "$input_name" ]; then
  echo "Error: Name cannot be empty."
  exit 1
fi

TARGET_NAME="${formatted_next_num}_${input_name}"
SRC_PATH="${ORDERS_DIR}/00000_boilerplate"
DEST_PATH="${ORDERS_DIR}/${TARGET_NAME}"

if [ ! -d "$SRC_PATH" ]; then
  echo "Error: Boilerplate directory '$SRC_PATH' not found."
  exit 1
fi

if [ -e "$DEST_PATH" ]; then
  echo "Error: Destination '$DEST_PATH' already exists."
  exit 1
fi

cp -r "$SRC_PATH" "$DEST_PATH"

echo "Created: $DEST_PATH"
