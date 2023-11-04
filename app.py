from flask import Flask, request, jsonify, make_response
import uuid
from datetime import datetime
import re

app = Flask(__name__)

#In-memory storage for receipt data (does not persist across restarts as per requirement)
receipts_data = {}

#Endpoint to process and store receipts, calculates points based on the rules provided
@app.route('/receipts/process', methods=['POST'])
def process_receipt():
    receipt = request.json

    #Generate a unique ID for the receipt using UUID4
    receipt_id = str(uuid.uuid4())

    try:
        points = calculate_points(receipt)
    except ReceiptValidationError as e:
        response = make_response(jsonify(error="The receipt is invalid", message=str(e)), 400)
    else:
        receipts_data[receipt_id] = points
        response = make_response(jsonify(id=receipt_id), 200)
    
    return response

#Endpoint to retrieve points for a given receipt ID
@app.route('/receipts/<receipt_id>/points', methods=['GET'])
def get_points(receipt_id):
    
    #Validate receipt ID format (no spaces)
    if not re.match('^\S+$', receipt_id):
        return make_response(jsonify(error="Invalid id format"), 400)
    
    points = receipts_data.get(receipt_id)
    if points is not None:
        response = make_response(jsonify(points=points), 200)
    else:
        response = make_response(jsonify(error="No receipt found for that id"), 404)
    
    return response

#Custom exception class for handling receipt validation errors
class ReceiptValidationError(Exception):
    pass


@app.errorhandler(Exception)
def handle_exception(e):
    return make_response(jsonify(error="Internal Server Error", message=str(e)), 500)

#Logic for calculating points based on receipt details
def calculate_points(receipt):
    points = 0
    required_keys = ['retailer', 'total', 'items', 'purchaseDate', 'purchaseTime']
    
    for key in required_keys:
        if key not in receipt:
            raise ReceiptValidationError(f"The key '{key}' is missing from the receipt.") 

    retailer = receipt['retailer']
    total = receipt['total']
    items = receipt['items']
    purchase_date = receipt['purchaseDate']
    purchase_time = receipt['purchaseTime']

    #Calculate points from retailer
    
    # Modified the regex pattern to match strings that start and end with a non-whitespace character
    # and allow for whitespace within the string. This accommodates retailer names with spaces,
    # such as "M&M Corner Market", while still ensuring the string does not begin or end with space.
    if not isinstance(retailer, str) or not re.match('^\\S(.*\\S)?$', retailer):
        raise ReceiptValidationError(f"Retailer is invalid: {retailer}")

    points += sum(c.isalnum() for c in retailer)

    #Calculate points from total
    if not isinstance(total, str) or not re.match('^\\d+\\.\\d{2}$', total):
        raise ReceiptValidationError(f"Total is invalid: {total}")

    total_float = float(total)
    if total_float.is_integer():
        points += 50
    if total_float % 0.25 == 0:
        points += 25
        
    #Calculate points from items
    if not isinstance(items, list):
        raise ReceiptValidationError(f"Items is invalid: {items}")

    if len(items) < 1:
        raise ReceiptValidationError(f"Items cannot be empty: {items}")

    points += (len(items) // 2) * 5

    required_item_keys = ['shortDescription', 'price']

    for i in range(len(items)):
        item = items[i]
        for key in required_item_keys:
            if key not in item:
                raise ReceiptValidationError(f"The key '{key}' is missing from item {i}.") 

        short_description = item["shortDescription"]
        price = item["price"]

        if not isinstance(short_description, str) or not re.match('^[\\w\\s\\-]+$', short_description):
            raise ReceiptValidationError(f"The short product description of item {i} is invalid: {short_description}")

        if not isinstance(price, str) or not re.match('^\\d+\\.\\d{2}$', price):
            raise ReceiptValidationError(f"The price of item {i} is invalid: {price}")

        if len(short_description.strip()) % 3 == 0:
            price_float = float(price) * 0.2
            points += int(price_float) + (price_float - int(price_float) > 0)

    #Calculate points from purchase date
    try:
        parsed_purchase_date = datetime.strptime(purchase_date, "%Y-%m-%d")
    except ValueError:
        raise ReceiptValidationError(f"Invalid purchase date format: {purchase_date}")
    
    if parsed_purchase_date.day % 2 == 1:
        points += 6

    #Calculate points from purchase time
    try:
        parsed_purchase_time = datetime.strptime(purchase_time, "%H:%M").time()
    except ValueError:
        raise ReceiptValidationError(f"Invalid purchase time format: {purchase_time}")

    #The following code awards 10 points to the receipt if the purchase time is strictly between 2:00pm and 4:00pm.
    #This means that purchases made exactly at 2:00pm or 4:00pm are not eligible for these points.
    start_time = datetime.strptime("14:00", "%H:%M").time()
    end_time = datetime.strptime("16:00", "%H:%M").time()
    
    if start_time < parsed_purchase_time < end_time:
        points += 10

    return points

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80)