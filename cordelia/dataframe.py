import pandas as pd
from cordelia.models import Dress, Rent, Customer, Maintenance
import matplotlib
import matplotlib.pyplot as plt 
from matplotlib.ticker import MultipleLocator
from io import BytesIO
import base64



def create_dataframes():

    dress_db = Dress.query.all()
    customer_db = Customer.query.all()
    rent_db = Rent.query.all()
    maintenance_db = Maintenance.query.all()

    if dress_db:
        dress_data = {
            'Id': [dress.id for dress in dress_db],
            'Size': [dress.size for dress in dress_db],
            'Color': [dress.color for dress in dress_db],
            'Style': [dress.style for dress in dress_db],
            'Brand': [dress.brand for dress in dress_db],
            'Cost': [dress.cost for dress in dress_db],
            'Date Added': [dress.dateAdded.strftime('%Y-%m-%d') for dress in dress_db],
            'Market Price': [dress.marketPrice for dress in dress_db],
            'Rent Price': [dress.rentPrice for dress in dress_db],
            'Rents for Returns': [dress.rentsForReturns for dress in dress_db],
            'Times Rented': [dress.timesRented for dress in dress_db],
            'Sellable': [dress.sellable for dress in dress_db],
            'Rent Status': [dress.rentStatus for dress in dress_db],
            'Maintenance Status': [dress.maintenanceStatus for dress in dress_db],
        }
        df_dress = pd.DataFrame(dress_data)

    if customer_db:
        customer_data = {
            'Id': [customer.id if customer.id else None for customer in customer_db],
            'Email': [customer.email for customer in customer_db],
            'Name': [customer.name for customer in customer_db],
            'Last Name': [customer.lastName for customer in customer_db],
            'Phone Number': [str(customer.phoneNumber) for customer in customer_db],
            'Date Added': [customer.dateAdded.strftime('%Y-%m-%d') for customer in customer_db],
        }
        df_customer = pd.DataFrame(customer_data)

    if rent_db:
        rent_data = {
            'Id': [rent.id for rent in rent_db],
            'Dress Id': [rent.dressId for rent in rent_db],
            'Customer Id': [rent.clientId for rent in rent_db],
            'Rent Date': [rent.rentDate.strftime('%Y-%m-%d') for rent in rent_db],
            'Return Date': [rent.returnDate.strftime('%Y-%m-%d') if rent.returnDate else '' for rent in rent_db],
            'Payment Total': [rent.paymentTotal for rent in rent_db],
        }
        df_rent = pd.DataFrame(rent_data)

    if maintenance_db:
        maintenance_data = {
            'Id': [maintenance.id for maintenance in maintenance_db],
            'Type': [maintenance.maintenance_type for maintenance in maintenance_db],
            'Date': [maintenance.date.strftime('%Y-%m-%d') for maintenance in maintenance_db],
            'Return Date': [maintenance.returnDate.strftime('%Y-%m-%d') if maintenance.returnDate else '' for maintenance in maintenance_db],
            'Total Cost': [maintenance.cost for maintenance in maintenance_db]
        }
        df_maintenance = pd.DataFrame(maintenance_data)
        
    return df_dress, df_customer, df_rent, df_maintenance


# Create Dataframes
df_dress, df_customer, df_rent, df_maintenance = create_dataframes()


# Plot number of rents by month
def monthly_rents():

    if not df_rent.empty:

        # Set the backend to non-GUI (e.g., Agg)
        plt.switch_backend('Agg')

        plt.style.use('ggplot')

        df_rent['Rent Date'] = pd.to_datetime(df_rent['Rent Date'])
        df_rent['YearMonth'] = df_rent['Rent Date'].dt.to_period('M')

        # Create a single figure with a specified size (width: 12 units, height: 6 units)
        fig, ax = plt.subplots(figsize=(8, 4))

        # Set the background color
        fig.set_facecolor('#DCC6B6') 

        # Count the occurrences of each unique 'YearMonth' value and sort them in ascending order.
        counts = df_rent['YearMonth'].value_counts().sort_index()
        # Extract the ordinal values (integer representations) of the 'YearMonth' periods for plotting.
        x_values = [period.ordinal for period in counts.index]

        # Plot the bar chart
        ax.bar(x_values, counts.values, color='#918272', label='Rents')

        # Plot the line chart
        ax.plot(x_values, counts.values, marker='o', linestyle='-', color='#a58d72')

        # Change the background color of the axes
        ax.set_facecolor("#b8b8b8dc")

        # Add labels and title
        ax.set_xlabel('Month')
        ax.set_ylabel('Number of Rents')
        ax.set_title('Rents per Month')

        # Customize the x-axis tick labels
        ax.set_xticks(x_values)
        ax.set_xticklabels([period.strftime('%b') for period in counts.index])

        # Show the legend
        ax.legend()

        # Save the plot to a BytesIO object
        buffer = BytesIO()
        plt.savefig(buffer, format="png")
        buffer.seek(0)

        # Convert the plot to a base64-encoded image
        image_data = base64.b64encode(buffer.read()).decode()
        buffer.close()

        return image_data
    
    return None


# Top customers plot # of rents and total spending
def top_customers():

    if not df_rent.empty:

        matplotlib.use('Agg')

        plt.style.use('seaborn-dark')

        # Group by customer ID and calculate total rentals and total spending
        customer_rentals = df_rent.groupby('Customer Id').agg({'Id': 'count', 'Payment Total': 'sum'})

        customer_rentals = customer_rentals.rename(columns={'Id': 'Total Rentals', 'Payment Total': 'Total Spending'})

        # Sort customers by the number of rentals
        top_customers_by_rentals = customer_rentals.sort_values(by='Total Rentals', ascending=False)

        # Sort customers by total spending
        top_customers_by_spending = customer_rentals.sort_values(by='Total Spending', ascending=False)

        # Create a subplot with two plots
        fig, axs = plt.subplots(1, 2, figsize=(8, 4))

        # Set the background color
        fig.set_facecolor('#DCC6B6') 

        # Plot the top customers by number of rentals
        top_customers_by_rentals.head(10).plot(kind='bar', y='Total Rentals', legend=True, ax=axs[0], color='#a58d72')
        axs[0].set_title('Top Customers by Number of Rentals')
        axs[0].set_xlabel('Customer ID')
        axs[0].set_ylabel('Total Rentals')

        # Set xticklabels straight
        axs[0].set_xticklabels(axs[0].get_xticklabels(), rotation=0)

        axs[0].set_facecolor("#b8b8b8dc")

        # Plot the top customers by total spending
        top_customers_by_spending.head(10).plot(kind='bar', y='Total Spending', legend=True, ax=axs[1], color='#a58d72')
        axs[1].set_title('Top Customers by Total Spending')
        axs[1].set_xlabel('Customer ID')
        axs[1].set_ylabel('Total Spending')

        # Set xticklabels straight
        axs[1].set_xticklabels(axs[1].get_xticklabels(), rotation=0)

        # Set the y-axis ticks in steps of 1000
        axs[1].yaxis.set_major_locator(MultipleLocator(1000))

        axs[1].set_facecolor("#b8b8b8dc")

        buffer = BytesIO()
        plt.savefig(buffer, format="png")
        buffer.seek(0)

        image_data = base64.b64encode(buffer.read()).decode()
        buffer.close()

        return image_data
    
    return None


# Plot earnings from Rents and Costs from Dress and Maintenance
def costs_vs_earnings():

    if not df_rent.empty and not df_maintenance.empty and not df_dress.empty:

        matplotlib.use('Agg')

        plt.style.use('seaborn')
        # Convert date columns to datetime
        df_rent['Rent Date'] = pd.to_datetime(df_rent['Rent Date'])
        df_maintenance['Date'] = pd.to_datetime(df_maintenance['Date'])
        df_dress['Date Added'] = pd.to_datetime(df_dress['Date Added'])

        # Create the 'YearMonth' column for each dataframe
        df_rent['YearMonth'] = df_rent['Rent Date'].dt.to_period('M')
        df_maintenance['YearMonth'] = df_maintenance['Date'].dt.to_period('M')
        df_dress['YearMonth'] = df_dress['Date Added'].dt.to_period('M')

        # Convert 'YearMonth' to ordinal for use as x-values
        df_costs_earnings = pd.DataFrame(index=df_rent['YearMonth'].unique())
        df_costs_earnings['YearMonth'] = df_costs_earnings.index.to_timestamp(freq='M').to_period('M').to_timestamp().map(lambda x: x.to_pydatetime().toordinal())

        # Group and aggregate the data by month
        rents_by_month = df_rent.groupby('YearMonth')['Payment Total'].sum()
        maintenance_by_month = df_maintenance.groupby('YearMonth')['Total Cost'].sum()
        dress_costs_by_month = df_dress.groupby('YearMonth')['Cost'].sum()

        # Combine the data into a single dataframe
        df_costs_earnings['Earnings'] = rents_by_month
        df_costs_earnings['Maintenance Costs'] = maintenance_by_month
        df_costs_earnings['Dress Acquisition Costs'] = dress_costs_by_month
        df_costs_earnings = df_costs_earnings.fillna(0)

        # Sort the data and x-axis labels in chronological order
        df_costs_earnings = df_costs_earnings.sort_index()
        index = [str(period.strftime('%b %Y')) for period in df_costs_earnings.index]

        # Create a list of numerical values for the x-axis
        x_values = list(range(len(index)))

        # Create a figure and axis
        fig, ax = plt.subplots(figsize=(8, 4))

        # Plot earnings
        ax.plot(x_values, df_costs_earnings['Earnings'], color='#00ff9d', label='Earnings')

        # Plot maintenance costs 
        ax.plot(x_values, df_costs_earnings['Maintenance Costs'],label='Maintenance Costs')

        # Plot dress acquisition costs
        ax.plot(x_values, df_costs_earnings['Dress Acquisition Costs'], label='Dress Acquisition Costs')

        # Set the x-axis labels
        ax.set_xticks(x_values)
        ax.set_xticklabels(index)

        # Add labels and title
        ax.set_xlabel('Month')
        ax.set_ylabel('Amount')
        ax.set_title('Costs vs. Earnings by Month')

        # Set the y-axis ticks in steps of 1000
        ax.yaxis.set_major_locator(MultipleLocator(5000))

        ax.legend()

        # Automatically adjust the subplot parameters.
        plt.tight_layout()

        buffer = BytesIO()
        plt.savefig(buffer, format="png")
        buffer.seek(0)

        image_data = base64.b64encode(buffer.read()).decode()
        buffer.close()

        return image_data
    
    return None
