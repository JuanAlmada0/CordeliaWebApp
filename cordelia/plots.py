import pandas as pd
from cordelia.models import Dress, Rent, Customer, Maintenance, Sale
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
    sale_db = Sale.query.all()

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

    if sale_db:
        sale_data = {
            'Id': [sale.id for sale in sale_db],
            'Customer Id': [sale.customer_id for sale in sale_db],
            'Dress Id': [sale.dress_id for sale in sale_db],
            'Sale Date': [sale.sale_date for sale in sale_db],
            'Sale Price': [sale.sale_price for sale in sale_db]
        }
        df_sale = pd.DataFrame(sale_data)
        
    return df_dress, df_customer, df_rent, df_maintenance, df_sale


df_dress, df_customer, df_rent, df_maintenance, df_sale= create_dataframes()



# Plot top customers by rents & spending
def top_customers():

    if not df_rent.empty:

        matplotlib.use('Agg')

        # Group by customer ID and calculate total rentals and total spending
        customer_rentals = df_rent.groupby('Customer Id').agg({'Id': 'count', 'Payment Total': 'sum'})

        customer_rentals = customer_rentals.rename(columns={'Id': 'Total Rentals', 'Payment Total': 'Total Spending'})

        # Sort customers by the number of rentals
        top_customers_by_rentals = customer_rentals.sort_values(by='Total Rentals', ascending=False)

        # Get the top 15 customers
        top_15_customers = top_customers_by_rentals.head(15)

        # Reverse the order of the top 15 customers
        top_15_customers = top_15_customers.iloc[::-1]

        # Sort customers by total spending
        top_customers_by_spending = customer_rentals.sort_values(by='Total Spending', ascending=False)

        plt.style.use('ggplot')

        # Create a subplot with two plots
        fig, axs = plt.subplots(1, 2, figsize=(9, 4))

        fig.set_facecolor('#DCC6B6') 

        # Plot the top customers by number of rentals
        top_15_customers.plot(kind='barh', y='Total Rentals', legend=True, ax=axs[0], color='#a58d72')
        axs[0].set_title('Top Customers by Number of Rentals')
        axs[0].set_ylabel('Customer ID')
        axs[0].set_xlabel('Total Rentals')

        # Set xticklabels straight
        axs[0].set_xticklabels(axs[0].get_xticklabels(), rotation=0)

        # Set the x-axis major locator to go up by 1
        axs[0].xaxis.set_major_locator(MultipleLocator(2))

        axs[0].set_facecolor("#b8b8b8dc")

        # Add grid lines 
        axs[0].grid(True)
        axs[0].grid(color='0.9')

        # Plot the top customers by total spending
        top_customers_by_spending.head(15).plot(kind='bar', y='Total Spending', legend=True, ax=axs[1], color='#a58d72')
        axs[1].set_title('Top Customers by Total Spending')
        axs[1].set_xlabel('Customer ID')
        axs[1].set_ylabel('Total Spending')

        # Set xticklabels straight
        axs[1].set_xticklabels(axs[1].get_xticklabels(), rotation=0)

        # Find the maximum and minimum spending among the top customers
        max_spending = top_customers_by_spending.head(15)['Total Spending'].max()
        min_spending = top_customers_by_spending.head(15)['Total Spending'].min()

        # Adjust the lower y-axis limit to be slightly below the minimum spending value
        axs[1].set_ylim(min_spending - 500, max_spending)

        # Set the y-axis major locator to go up by 500
        axs[1].yaxis.set_major_locator(MultipleLocator(1000))

        axs[1].set_facecolor("#b8b8b8dc")

        # Add grid lines
        axs[1].grid(True)
        axs[1].grid(color='0.9')

        plt.tight_layout()

        buffer = BytesIO()
        plt.savefig(buffer, format="png")
        buffer.seek(0)

        image_data = base64.b64encode(buffer.read()).decode()
        buffer.close()

        return image_data
    
    return None



def costs_vs_earnings():

    if not df_rent.empty and not df_maintenance.empty and not df_dress.empty and not df_sale.empty:

        matplotlib.use('Agg')

        # Convert date columns to datetime
        df_rent['Rent Date'] = pd.to_datetime(df_rent['Rent Date'])
        df_maintenance['Date'] = pd.to_datetime(df_maintenance['Date'])
        df_dress['Date Added'] = pd.to_datetime(df_dress['Date Added'])
        df_sale['Sale Date'] = pd.to_datetime(df_sale['Sale Date'])

        # Create the 'YearMonth' column for each dataframe
        df_rent['YearMonth'] = df_rent['Rent Date'].dt.to_period('M')
        df_maintenance['YearMonth'] = df_maintenance['Date'].dt.to_period('M')
        df_dress['YearMonth'] = df_dress['Date Added'].dt.to_period('M')
        df_sale['YearMonth'] = df_sale['Sale Date'].dt.to_period('M')

        # Convert 'YearMonth' to ordinal for use as x-values
        df_costs_earnings = pd.DataFrame(index=df_rent['YearMonth'].unique())
        df_costs_earnings['YearMonth'] = df_costs_earnings.index.to_timestamp(freq='M').to_period('M').to_timestamp().map(lambda x: x.to_pydatetime().toordinal())

        # Group and aggregate the data by month
        rents_by_month = df_rent.groupby('YearMonth')['Payment Total'].sum()
        maintenance_by_month = df_maintenance.groupby('YearMonth')['Total Cost'].sum()
        dress_costs_by_month = df_dress.groupby('YearMonth')['Cost'].sum()
        sales_by_month = df_sale.groupby('YearMonth')['Sale Price'].sum()

        # Combine the data into a single dataframe
        df_costs_earnings['Earnings'] = rents_by_month
        df_costs_earnings['Maintenance Costs'] = maintenance_by_month
        df_costs_earnings['Dress Acquisition Costs'] = dress_costs_by_month
        df_costs_earnings['Sales'] = sales_by_month
        df_costs_earnings = df_costs_earnings.fillna(0)

        # Sort the data and x-axis labels in chronological order
        df_costs_earnings = df_costs_earnings.sort_index()
        index = [str(period.strftime('%b %Y')) for period in df_costs_earnings.index]

        # Create a list of numerical values for the x-axis
        x_values = list(range(len(index)))

        plt.style.use('ggplot')

        fig, ax = plt.subplots(figsize=(9, 4))

        fig.set_facecolor('black')

        ax.grid(color='#2A3459')  # bluish dark grey

        colors = [
            '#08F7FE',  # teal/cyan
            '#FE53BB',  # pink
            '#00ff41',  # matrix green
            '#FFD700',  # gold for sales
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
        ax.plot(x_values, df_costs_earnings['Dress Acquisition Costs'], marker='o', linestyle='--', color=colors[1], label='Dress Acquisition Costs', linewidth=1)

        # Plot sales with a solid line style and marker
        ax.plot(x_values, df_costs_earnings['Sales'], marker='o', linestyle='-', color=colors[3], label='Sales', linewidth=1)

        # Set the x-axis labels
        ax.set_xticks(x_values)
        ax.set_xticklabels(index, rotation=0)

        # Set the y-axis labels with comma as the thousands separator
        ax.get_yaxis().set_major_formatter(FuncFormatter(lambda x, p: format(int(x), ',')))

        # Set the y-axis major locator to go up by 5k
        ax.yaxis.set_major_locator(MultipleLocator(10000))

        # Add labels and title
        ax.set_ylabel('Amount')
        ax.set_title('Costs vs. Earnings', color='0.9')

        # Configure the legend with white text color
        legend = ax.legend(labels=['Earnings', 'Maintenance Costs', 'Dress Acquisition Costs', 'Sales'], loc='best', fontsize='small')
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




def plot_combined_statistics():

    if df_rent is None or df_rent.empty:
        return None

    matplotlib.use('Agg')
    
    plt.style.use('seaborn-dark')

    # Create a subplot with two plots
    fig, axs = plt.subplots(1, 2, figsize=(9, 4))

    fig.set_facecolor('#DCC6B6')

    # Plot number of rents by month
    df_rent['Rent Date'] = pd.to_datetime(df_rent['Rent Date'])
    df_rent['YearMonth'] = df_rent['Rent Date'].dt.to_period('M')

    counts = df_rent['YearMonth'].value_counts().sort_index()
    x_values = [period.ordinal for period in counts.index]

    axs[0].bar(x_values, counts.values, color='#918272', label='Rents')
    axs[0].plot(x_values, counts.values, marker='o', linestyle='-', color='#a58d72')

    axs[0].set_facecolor("#b8b8b8dc")
    axs[0].set_xlabel('Month')
    axs[0].set_ylabel('Number of Rents')
    axs[0].set_title('Rents per Month')
    axs[0].set_xticks(x_values)
    axs[0].set_xticklabels([period.strftime('%b') for period in counts.index])
    axs[0].legend()

    # Set the y-axis major locator to go up by 5k
    axs[0].yaxis.set_major_locator(MultipleLocator(4))

    # Find the minimum number of rents per month
    min_rents = counts.min()
    
    # Adjust the lower y-axis limit to be slightly less than the month with min rents
    axs[0].set_ylim(min_rents - 4)

    # Add grid lines
    axs[0].grid(True)
    axs[0].grid(color='0.9')

    # Plot the pie chart
    day_of_week_counts = df_rent['Rent Date'].dt.day_name().value_counts()
    labels = day_of_week_counts.index
    sizes = day_of_week_counts.values
    colors = ['#08F7FE', '#FE53BB', '#00ff41', '#ff9900', '#b64fff', '#FA8072']
    explode = (0.075, 0.05, 0.025, 0, 0, 0)

    axs[1].pie(sizes, explode=explode, labels=labels, colors=colors, autopct='%1.1f%%', shadow=True, startangle=140)
    axs[1].axis('equal')
    axs[1].set_title('Rents by Weekday', color='black', loc='center')

    for text in axs[1].texts:
        text.set_color('black')

    plt.tight_layout()

    buffer = BytesIO()
    plt.savefig(buffer, format="png")
    buffer.seek(0)

    image_data = base64.b64encode(buffer.read()).decode()
    buffer.close()

    return image_data



plt.style.use('default')