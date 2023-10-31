import pandas as pd
from cordelia.models import Dress, Rent, Customer, Maintenance
import matplotlib
import matplotlib.pyplot as plt 
from matplotlib.ticker import FuncFormatter, MultipleLocator
from io import BytesIO
import base64


# Create Dataframes
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

        # Automatically adjust the subplot parameters.
        plt.tight_layout()

        # Save the plot to a BytesIO object
        buffer = BytesIO()
        plt.savefig(buffer, format="png")
        buffer.seek(0)

        # Convert the plot to a base64-encoded image
        image_data = base64.b64encode(buffer.read()).decode()
        buffer.close()

        return image_data
    
    return None


# Plot top customers by rents & spending
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

        # Find the maximum and minimum spending among the top customers
        max_spending = top_customers_by_spending.head(10)['Total Spending'].max()
        min_spending = top_customers_by_spending.head(10)['Total Spending'].min()

        # Adjust the lower y-axis limit to be slightly below the minimum spending value
        axs[1].set_ylim(min_spending - 100, max_spending)

        axs[1].set_facecolor("#b8b8b8dc")

        plt.tight_layout()

        buffer = BytesIO()
        plt.savefig(buffer, format="png")
        buffer.seek(0)

        image_data = base64.b64encode(buffer.read()).decode()
        buffer.close()

        return image_data
    
    return None


# Plot earnings and costs from dress and maintenance
def costs_vs_earnings():

    if not df_rent.empty and not df_maintenance.empty and not df_dress.empty:

        matplotlib.use('Agg')

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

        plt.style.use('seaborn-dark')

        fig, ax = plt.subplots(figsize=(8, 4))

        fig.set_facecolor('black')
        ax.grid(color='#2A3459')  # bluish dark grey

        colors = [
            '#08F7FE',  # teal/cyan
            '#FE53BB',  # pink
            '#00ff41',  # matrix green
        ]

        ax.set_facecolor('black')
        ax.xaxis.label.set_color('0.9')  # Text color
        ax.yaxis.label.set_color('0.9')  # Text color
        ax.xaxis.label.set_color('0.9')  # Text color
        ax.tick_params(axis='x', colors='0.9')  # X-axis tick color
        ax.tick_params(axis='y', colors='0.9')  # Y-axis tick color

        # Plot earnings with a solid line style and marker
        ax.plot(x_values, df_costs_earnings['Earnings'], marker='o', color=colors[2], linestyle='-', label='Earnings', linewidth=1)

        # Plot maintenance costs with a dashed line style and marker
        ax.plot(x_values, df_costs_earnings['Maintenance Costs'], marker='o', linestyle='--', color=colors[0], label='Maintenance Costs', linewidth=1)

        # Plot dress acquisition costs with a solid line style and marker
        ax.plot(x_values, df_costs_earnings['Dress Acquisition Costs'], marker='o', linestyle='-', color=colors[1], label='Dress Acquisition Costs', linewidth=1)

        # Set the x-axis labels
        ax.set_xticks(x_values)
        ax.set_xticklabels(index, rotation=0)

        # Set the y-axis labels with comma as the thousands separator
        ax.get_yaxis().set_major_formatter(FuncFormatter(lambda x, p: format(int(x), ',')))

        # Set the y-axis major locator to go up by 5k
        ax.yaxis.set_major_locator(MultipleLocator(5000))

        # Add labels and title
        ax.set_ylabel('Amount')
        ax.set_title('Costs vs. Earnings', color='0.9')

        # Configure the legend with white text color
        legend = ax.legend(labels=['Earnings', 'Maintenance Costs', 'Dress Acquisition Costs'], loc='best', fontsize='small')
        for text in legend.get_texts():
            text.set_color('white')

        plt.tight_layout()

        buffer = BytesIO()
        plt.savefig(buffer, format="png")
        buffer.seek(0)

        image_data = base64.b64encode(buffer.read()).decode()
        buffer.close()

        return image_data

    return None



# Plot percentage of rents by weekday
def rents_by_weekday():

    if df_rent is None or df_rent.empty:
        return None

    matplotlib.use('Agg')

    # Convert the 'Rent Date' column to datetime
    df_rent['Rent Date'] = pd.to_datetime(df_rent['Rent Date'])

    # Group and count rents by day of the week
    day_of_week_counts = df_rent['Rent Date'].dt.day_name().value_counts()

    # Create a pie chart
    labels = day_of_week_counts.index
    sizes = day_of_week_counts.values
    colors = ['#08F7FE', '#FE53BB', '#00ff41', '#8B4513', '#FFD700', '#FA8072', '#6495ED']
    explode = (0.1, 0, 0, 0, 0, 0, 0)  # explode the 1st slice

    plt.style.use('seaborn-dark')

    fig, ax = plt.subplots(figsize=(8, 4))

    fig.set_facecolor('grey')

    ax.set_facecolor('white')

    # Plot the pie chart
    ax.pie(sizes, explode=explode, labels=labels, colors=colors, autopct='%1.1f%%', shadow=True, startangle=140)
    ax.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.

    ax.set_title('Rents by Weekday', color='0.9', loc='left')

    # Set label color
    for text in ax.texts:
        text.set_color('black')

    plt.tight_layout()

    buffer = BytesIO()
    plt.savefig(buffer, format="png")
    buffer.seek(0)

    image_data = base64.b64encode(buffer.read()).decode()
    buffer.close()

    return image_data



plt.style.use('default')