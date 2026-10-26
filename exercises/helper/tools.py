import pandas as pd
import ipywidgets as widgets
import yfinance as yf
from io import StringIO
import requests
import matplotlib.pyplot as plt
import numpy as np
import scipy.stats as st


class StockSearch:

    def __init__(self):
        # 1. Fetch data first
        self.sp_tickers = self.get_sp500_tickers()

        self.selected_tickers = []

        # 2. Adding tickers
        self.ticker_input = widgets.Combobox(
            placeholder="Type a ticker (e.g. AAPL)",
            options=self.sp_tickers,
            description="Ticker:",
            ensure_option=False,
        )

        self.add_btn = widgets.Button(
            description="Add", icon="plus", button_style="info"
        )

        self.selected_box = widgets.Select(
            options=self.selected_tickers,
            description="Selected:",
            disabled=False,
        )

        self.add_btn.on_click(self.add_ticker)

        # Adding Calendar
        self.start_date = widgets.DatePicker(description="Start Date")
        self.end_date = widgets.DatePicker(description="End Date")

        self.interval_select = widgets.Dropdown(
    options=["1d", "5d", "1wk", "1mo", "3mo"],
    value="1d",
    description="Interval:",
)

        # 3. Display
        self.show()

    def get_sp500_tickers(self):
        url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
        headers = {"User-Agent": "Mozilla/5.0"}
    
        response = requests.get(url, headers=headers)
        table = pd.read_html(StringIO(response.text))
    
        return table[0]["Symbol"].tolist()

    def add_ticker(self, _):
        ticker = self.ticker_input.value.strip().upper()

        # Add only if not empty and not already added
        if ticker and ticker not in self.selected_tickers:
            self.selected_tickers.append(ticker)
            # Re-assign options to refresh the display box
            self.selected_box.options = self.selected_tickers
            # Clear text field for next entry
            self.ticker_input.value = ""


    def show(self):
        ticker_row = widgets.HBox([self.ticker_input, self.add_btn])

        ui = widgets.VBox(
            [
                ticker_row,
                self.selected_box,
                self.start_date,
                self.end_date,
                self.interval_select,
            ]
        )
        display(ui)

    @property
    def start(self):
        return self.start_date.value
    
    
    @property
    def end(self):
        return self.end_date.value
    
    
    @property
    def tickers(self):
        return self.selected_tickers

    @tickers.setter
    def tickers(self, new_tickers):
        # Allow passing a single string like 'AAPL' or a list ['AAPL', 'MSFT']
        if isinstance(new_tickers, str):
            new_tickers = [new_tickers]
            
        self.selected_tickers = list(new_tickers)
        
        # Keep the UI box in sync with the override:
        self.selected_box.options = self.selected_tickers

    @property
    def interval(self):
        return self.interval_select.value

    @property
    def data(self):
        df = yf.Tickers(self.tickers).download(start=self.start, end=self.end, interval= self.interval)
        df = df[['Close', 'Volume']]
        return df
        

def summary_statistics_table(dataframe):
    import pandas as pd
    """
    This helper-function takes a DataFrame of Daily Returns
    with columns of Ticker-names, and rows of dates.
    Returns a DataFrame with summary statistics:
    'Mean', 'Median', 'Standard-Deviation', 'Skewness', 'Kurtosis', 'Min', 'Max'
    utilizing pandas built-in .mean(), .median(), ..., etc. methods
    
    """
    
    columns = dataframe.columns

    index_list = ['Mean', 'Median', 'Standard-Deviation', 'Skewness', 'Kurtosis', 'Min', 'Max']
    
    member_stats = pd.DataFrame(data=None, index=index_list)
    for col in columns:
        rtn:pd.Series = dataframe[col]
        
        mean = rtn.mean()
        median = rtn.median()
        std = rtn.std()
        skew = rtn.skew()
        kurt = rtn.kurt()
        min_rtn = rtn.min()
        max_rtn = rtn.max()



        stats = pd.Series(
            name= col,
            data = [
                mean,
                median,
                std,
                skew,
                kurt,
                min_rtn,
                max_rtn
            ],
            index = index_list,
        )
        member_stats = member_stats.join(stats)

    return member_stats

def return_histograms(dataframe: pd.DataFrame):
    """
    This will display a series of histograms with summary statistics labeled.
    It accepts a pandas DataFrame with Returns data. Row Index of dates. 
    Columns of different tickers.
    It Depends on our helper-function summary_statistics_table()
    """
    import pandas as pd

    stats = summary_statistics_table(dataframe)

    columns = dataframe.columns

    for col in columns:
        plt.grid()
        counts,bins,_ = plt.hist(
            dataframe[col],
            bins = 100,
            color = 'deeppink',
            edgecolor = 'black',
            linewidth = 0.2,
            alpha=0.3
        )
        
        max_occ = counts.max()
        
        #Plot our mean on distribution
        mean = stats[col]['Mean']
        plt.vlines(
            mean,
            ymin=0,
            ymax= 0.95* max_occ,
            color='purple', 
            label=f"Mean={mean:.4f}")
        #Plot +/- standard-deviation
        std = stats[col]['Standard-Deviation']
        std_up = mean + std
        std_down = mean - std
        plt.vlines(
            [std_up, std_down],
            ymin=0,
            ymax= 0.4* max_occ,
            color='blue', 
            alpha=0.7,
            label=rf"$\sigma = \pm${std:.4f}")
        #Plot 2-sigma moves
        std_up2 = mean + std*2
        std_down2 = mean - std*2
        plt.vlines(
            [std_up2, std_down2],
            ymin=0,
            ymax= 0.2* max_occ,
            color='blueviolet', 
            alpha=0.7,
            label=rf"2$\sigma = \pm${std*2:.4f}")
        #Plot 3-sigma moves
        std_up2 = mean + std*3
        std_down2 = mean - std*3
        plt.vlines(
            [std_up2, std_down2],
            ymin=0,
            ymax= 0.1* max_occ,
            color='red',
            alpha=0.7,
            label=rf"3$\sigma =  \pm${std*3:.4f}")

        #Overlay a Bell-Curve

        xmin, xmax = plt.xlim()
        x = np.linspace(xmin, xmax, 100)

        p = st.norm.pdf(x, mean, std)



        bin_width = bins[1] - bins[0]
        scaled_p = p * len(dataframe[col].dropna()) * bin_width
        plt.plot(x,scaled_p, color='black', alpha=0.3, label="Normal-Dist")

        #Clean Up plot and label
        plt.ylabel("# of occurrences")
        plt.xlabel("Return in %-decimal: ie. 1% = 0.01")
        plt.title(f"{col} Return Distribution")
        plt.legend()
        
        plt.show()