import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

st.set_page_config(page_title="Loan Amortization Calculator", layout="wide")

st.title("🏦 Loan Amortization Calculator")
st.markdown("Calculate your loan payments and visualize how they're allocated between principal and interest over time.")

# Sidebar for inputs
st.sidebar.header("Loan Parameters")
principal = st.sidebar.number_input("Loan Amount ($)", min_value=1000, max_value=1000000, value=90000, step=1000)
annual_interest_rate = st.sidebar.number_input("Annual Interest Rate (%)", min_value=0.1, max_value=30.0, value=17.0, step=0.1) / 100
loan_term_years = st.sidebar.number_input("Loan Term (Years)", min_value=1, max_value=30, value=5, step=1)
fixed_monthly_payment = st.sidebar.number_input("Fixed Monthly Payment ($)", min_value=100, max_value=50000, value=1500, step=50)

# Calculate monthly interest rate
monthly_interest_rate = annual_interest_rate / 12

# Display key metrics
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Loan Amount", f"${principal:,.2f}")
with col2:
    st.metric("Annual Interest Rate", f"{annual_interest_rate*100:.1f}%")
with col3:
    st.metric("Monthly Interest Rate", f"{monthly_interest_rate*100:.3f}%")
with col4:
    st.metric("Monthly Payment", f"${fixed_monthly_payment:,.2f}")

# Calculate amortization schedule
def calculate_amortization(principal, monthly_rate, monthly_payment, max_years):
    schedule = []
    remaining_principal = principal
    total_interest_paid = 0
    total_principal_paid = 0
    month_num = 0
    
    for year in range(1, max_years + 1):
        for month in range(1, 13):
            month_num += 1
            
            # Calculate interest for this month
            interest_payment = round(remaining_principal * monthly_rate, 2)
            
            # Calculate principal payment
            principal_payment = round(monthly_payment - interest_payment, 2)
            
            # Handle case where principal payment exceeds remaining balance
            if principal_payment > remaining_principal:
                principal_payment = remaining_principal
                actual_payment = interest_payment + principal_payment
            else:
                actual_payment = monthly_payment
            
            # Update totals
            total_interest_paid += interest_payment
            total_principal_paid += principal_payment
            remaining_principal -= principal_payment
            
            # Store the data
            schedule.append({
                'Month': month_num,
                'Year': year,
                'Payment': actual_payment,
                'Interest': interest_payment,
                'Principal': principal_payment,
                'Remaining_Balance': round(remaining_principal, 2),
                'Total_Interest': round(total_interest_paid, 2),
                'Total_Principal': round(total_principal_paid, 2)
            })
            
            # Break if loan is paid off
            if remaining_principal <= 0:
                return schedule, total_interest_paid, total_principal_paid, month_num
    
    return schedule, total_interest_paid, total_principal_paid, month_num

# Calculate the schedule
schedule, total_interest, total_principal, payoff_months = calculate_amortization(
    principal, monthly_interest_rate, fixed_monthly_payment, loan_term_years
)

# Create DataFrame
df = pd.DataFrame(schedule)

# Summary metrics
st.subheader("📊 Loan Summary")
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Total Interest Paid", f"${total_interest:,.2f}")
with col2:
    st.metric("Total Principal Paid", f"${total_principal:,.2f}")
with col3:
    st.metric("Total Payments", f"${total_interest + total_principal:,.2f}")
with col4:
    payoff_years = payoff_months // 12
    payoff_remaining_months = payoff_months % 12
    st.metric("Payoff Time", f"{payoff_years}y {payoff_remaining_months}m")

# Check if loan is paid off within term
if df.iloc[-1]['Remaining_Balance'] > 0:
    st.warning(f"⚠️ Loan will not be fully paid off in {loan_term_years} years. Remaining balance: ${df.iloc[-1]['Remaining_Balance']:,.2f}")
else:
    st.success(f"✅ Loan will be paid off in {payoff_years} years and {payoff_remaining_months} months!")

# Create visualizations
st.subheader("📈 Payment Breakdown Over Time")

# Create subplots
fig = make_subplots(
    rows=2, cols=2,
    subplot_titles=('Monthly Payment Allocation', 'Remaining Balance Over Time', 
                   'Cumulative Payments', 'Interest vs Principal per Payment'),
    specs=[[{"secondary_y": False}, {"secondary_y": False}],
           [{"secondary_y": False}, {"secondary_y": False}]]
)

# Monthly payment allocation (stacked bar)
fig.add_trace(
    go.Scatter(x=df['Month'], y=df['Interest'], name='Interest', 
               fill='tonexty', fillcolor='rgba(255, 99, 132, 0.7)'),
    row=1, col=1
)
fig.add_trace(
    go.Scatter(x=df['Month'], y=df['Principal'], name='Principal', 
               fill='tozeroy', fillcolor='rgba(54, 162, 235, 0.7)'),
    row=1, col=1
)

# Remaining balance
fig.add_trace(
    go.Scatter(x=df['Month'], y=df['Remaining_Balance'], name='Remaining Balance',
               line=dict(color='green', width=3)),
    row=1, col=2
)

# Cumulative payments
fig.add_trace(
    go.Scatter(x=df['Month'], y=df['Total_Interest'], name='Cumulative Interest',
               line=dict(color='red', width=2)),
    row=2, col=1
)
fig.add_trace(
    go.Scatter(x=df['Month'], y=df['Total_Principal'], name='Cumulative Principal',
               line=dict(color='blue', width=2)),
    row=2, col=1
)

# Interest vs Principal ratio
fig.add_trace(
    go.Bar(x=df['Month'][:min(60, len(df))], y=df['Interest'][:min(60, len(df))], 
           name='Interest (First 5 Years)', marker_color='rgba(255, 99, 132, 0.8)'),
    row=2, col=2
)
fig.add_trace(
    go.Bar(x=df['Month'][:min(60, len(df))], y=df['Principal'][:min(60, len(df))], 
           name='Principal (First 5 Years)', marker_color='rgba(54, 162, 235, 0.8)'),
    row=2, col=2
)

# Update layout
fig.update_layout(height=800, showlegend=True, title_text="Loan Amortization Analysis")
fig.update_xaxes(title_text="Month", row=2, col=1)
fig.update_xaxes(title_text="Month", row=2, col=2)
fig.update_yaxes(title_text="Amount ($)", row=1, col=1)
fig.update_yaxes(title_text="Balance ($)", row=1, col=2)
fig.update_yaxes(title_text="Cumulative ($)", row=2, col=1)
fig.update_yaxes(title_text="Monthly Amount ($)", row=2, col=2)

st.plotly_chart(fig, use_container_width=True)

# Payment schedule table
st.subheader("📋 Detailed Payment Schedule")

# Add filters
col1, col2 = st.columns(2)
with col1:
    show_year = st.selectbox("Filter by Year", ["All Years"] + [f"Year {i}" for i in range(1, max(df['Year']) + 1)])
with col2:
    show_months = st.slider("Show first N months", 12, len(df), min(60, len(df)))

# Filter dataframe
if show_year != "All Years":
    year_num = int(show_year.split()[1])
    filtered_df = df[df['Year'] == year_num].head(show_months)
else:
    filtered_df = df.head(show_months)

# Format the dataframe for display
display_df = filtered_df.copy()
display_df['Payment'] = display_df['Payment'].apply(lambda x: f"${x:,.2f}")
display_df['Interest'] = display_df['Interest'].apply(lambda x: f"${x:,.2f}")
display_df['Principal'] = display_df['Principal'].apply(lambda x: f"${x:,.2f}")
display_df['Remaining_Balance'] = display_df['Remaining_Balance'].apply(lambda x: f"${x:,.2f}")

st.dataframe(
    display_df[['Month', 'Year', 'Payment', 'Interest', 'Principal', 'Remaining_Balance']],
    use_container_width=True,
    hide_index=True
)

# Download button
if st.button("📥 Download Full Schedule as CSV"):
    csv = df.to_csv(index=False)
    st.download_button(
        label="Download CSV",
        data=csv,
        file_name=f"loan_amortization_schedule_{principal}_{annual_interest_rate*100:.1f}pct.csv",
        mime="text/csv"
    )

# Additional insights
st.subheader("💡 Key Insights")
if len(df) > 0:
    first_payment_interest = df.iloc[0]['Interest']
    first_payment_principal = df.iloc[0]['Principal']
    interest_percentage_first = (first_payment_interest / fixed_monthly_payment) * 100
    
    if len(df) >= 12:
        year_one_interest = df[df['Year'] == 1]['Interest'].sum()
        year_one_principal = df[df['Year'] == 1]['Principal'].sum()
        
        st.write(f"• **First payment breakdown**: {interest_percentage_first:.1f}% goes to interest ({first_payment_interest:,.2f}) vs {100-interest_percentage_first:.1f}% to principal ({first_payment_principal:,.2f})")
        st.write(f"• **Year 1 totals**: {year_one_interest:,.2f} in interest, {year_one_principal:,.2f} in principal")
    
    if df.iloc[-1]['Remaining_Balance'] <= 0:
        interest_to_principal_ratio = total_interest / principal
        st.write(f"• **Total cost**: You'll pay {total_interest:,.2f} in interest over the life of the loan ({interest_to_principal_ratio:.1%} of the original principal)")
    
    st.write(f"• **Early payoff benefit**: Making extra principal payments can significantly reduce total interest paid")
