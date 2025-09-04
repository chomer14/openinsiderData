# Generate table of insiders with [id | name] (SELECT DISTINCT insider_name FROM transactions_bronze)
# Generate table of companies with [id | ticker | name]
# Explore solutions to what role each user plays in a company
# - Potentially another table that relates [transaction id | personnal role]
# - Would require another table of possible roles (E.g. CFO, CEO, 10%...)

# Remove X, filing date, ticker, company name, insider name, dOwnedPc
# replace trade type with boolean
# add columns to relate insiders and companies
