"""
Daniel Wong
CIS41B
Lab4 - Multithreading
"""

import requests
from bs4 import BeautifulSoup
import json
import os
import threading
import time
import queue

import tkinter as tk
import tkinter.filedialog
import tkinter.messagebox as tkmb

class MainWindow(tk.Tk):
    regions = {'Napa': 'North Bay', 'Sonoma': 'North Bay', 'Santa Cruz': 'The Coast', 'Monterey': 'The Coast',
               'Berkeley': 'East Bay', 'Livermore': 'East Bay', 'San Francisco': 'Peninsula', 'San Mateo': 'Peninsula',
               'San Jose': 'South Bay', 'Los Gatos': 'South Bay'}
    geo_root_url = "https://geocoding-api.open-meteo.com/v1/search"
    weather_root_url = "https://api.open-meteo.com/v1/forecast"
    requested_keys = ['time', 'temperature_2m_max', 'temperature_2m_min', 'uv_index_max', 'wind_speed_10m_max']
    def __init__(self):
        '''Constructor for the MainWindow Class'''
        super().__init__()
        self._location_dict = {}
        self.indices = None
        self.weather_data = set()
        self._lock = threading.Lock()
        self.q = queue.Queue() #EC Code
        self.e = threading.Event() #EC Code
        self._dict = {}
        self._data_list = [] 

        self.title("Travel Weather App")
        tk.Label(self, text="Look up weather at your destination")

        self.populate_city_data()
        self.create_ui()

    def populate_city_data(self):
        '''Check if data.json already exist
           - If not exist, request web data and create data
           - If exist, call get_weather_data to read from json '''
        
        filepath = os.path.join(os.path.dirname(__file__), 'data.json')
        if not os.path.isfile(filepath): #If file not exist, request data and create json 
            self.request_web_data()
            self.create_json()
        self._location_dict = self.get_weather_data()

    def create_ui(self):
        '''Create a list button for the number of locations in the dictionary'''
        tk.Label(self, text='Look up weather at your desintation', fg="blue", font=("Arial", 15)).grid(column=0, row=0)
        tk.Label(self, text='Select destinations then click Submit', fg="blue").grid(column=0, row=1)
        self.LB = tk.Listbox(self, height=20, width=40, selectmode="multiple")
        self.LB.grid(column=0, row=3)

        for city in self._location_dict.keys():
            region = self.regions[city]
            self.LB.insert(tk.END, f"{region}: {city}")
        self.LB.grid()

        B = tk.Button(self, text="Submit", command=self.selection)
        B.grid(row=11,padx = 215,sticky = 'w')

        self.grab_set() # disable event for other windows
        self.focus_set() # set focus on current window
        self.protocol("WM_DELETE_WINDOW", self.save_to_file)
        
    def selection(self):
        '''If Listboxes have been selected, create threads and send them to fetch'''
        self.indices = self.LB.curselection()
        self.LB.selection_clear(0, tk.END) #Automatically clear tk.Button after selection
        if self.indices:
            thread_list = []
            for idx in self.indices:
                city, coords = list(self._location_dict.items())[idx]
                latitude, longitude = coords
                t = threading.Thread(target = self._request_weather_data, args = (city, latitude, longitude))
                thread_list.append(t)
        
            start = time.time()
            for t in thread_list:
                t.start()
            # Original code (not EC)
            # This bruteforce/simplistic solution is not as efficient in creating DisplayWindows, it waits for all the threads to finish
            # Before beginning to execute the Display Windows
            '''
            for t in thread_list:
                t.join()
            for idx in self.indices:
                city, coords = list(self._location_dict.items())[idx]
                data = self._dict[city]
                displaywindow = DisplayWindow(self, city, data)
            '''

            # EC code:
            #This solution is significantly more efficient in creating DisplayWindows, as it does not wait for all threads to finish before generating DisplayWindows.
            #Rather, as each thread is finished, it pushes the data into the threading queue, and the main thread is continually waiting as the consumer 
            #to generate DisplayWindows as soon as one arrives in the queue.  
            n = len(thread_list)
            while not self.e.is_set() or n > 0:
                if self.e.is_set() and n == 0:
                    self.e.clear()
                if not self.q.empty():
                    city, data = self.q.get()
                    n -= 1
                    displaywindow = DisplayWindow(self, city, data)
            print("elapsed time:", round(time.time() - start, 2))
            
            self.indices = None

    def get_selected_data(self):
        '''return weather data'''
        return self.weather_data
    
    def save_to_file(self):
        '''Save resulting from DisplayWindow into weather txt file'''
        is_save = tkinter.messagebox.askokcancel(title=None, message='Save your results in a directory of your choice?')
        if is_save:
            chosenpath = tk.filedialog.askdirectory(initialdir = '.')
            filename = os.path.join(chosenpath, 'weather.txt')
            fh = open(filename,'a')

            for line in self.weather_data:
                fh.write(line + "\n")
            fh.close()
            
            msg = "Your search result is saved in weather.txt in " + chosenpath
        self.quit()
        self.destroy()

    def request_web_data(self):
        '''Start and join multiprocessing threads to request web data'''
        thread_list = []
        for city in self.regions.keys():
            t = threading.Thread(target = self._request_web_data, args = (city, ))
            thread_list.append(t)
        start = time.time()
        for t in thread_list:
            t.start()
        for t in thread_list:
            t.join()
        print("elapsed time:", round(time.time() - start, 2))

    def _request_web_data(self, city):
        '''Request data from the web and append data to a list'''
        param1 = "?name="
        param2 = "&count=10"
        param3 = "&language=en"
        param4 = "&format=json"
        page = requests.get(self.geo_root_url + param1 + city + param2 + param3 + param4) 

        with self._lock:
            json_dict = page.json()
            data_results = json_dict["results"]
            for item in data_results:
                if "country" in item and item["country"] == "United States" and item["admin1"] == "California":
                    self._data_list.append(item)
        
    def create_json(self):
        '''Opens the json file and inputs the data from the list of dictionary data'''
        filepath = os.path.join(os.path.dirname(__file__), 'data.json')
        with open(filepath, 'w') as fh: # KEEP, this will create it in the same directory where you run this lab4.py
            json.dump(self._data_list, fh, indent=3)

    def _request_weather_data(self, city, latitude, longitude):
        '''Request Weather API Data'''
        param1 = "?latitude="
        param2 = "&longitude="
        param3 = "&daily=weather_code,temperature_2m_max,temperature_2m_min,uv_index_max,wind_speed_10m_max&forecast_days=5&temperature_unit=fahrenheit&wind_speed_unit=mph&precipitation_unit=inch&timezone=America%2FLos_Angeles"

        page = requests.get(self.weather_root_url + param1 + str(latitude) + param2 + str(longitude) + param3) 
        output = page.json()['daily']
        self.q.put((city,output))
        self.e.set() #EC code

    def get_weather_data(self):
        '''Fetch data from the JSON File'''
        with open(os.path.join(os.path.dirname(__file__), 'data.json'), 'r') as fh:
            self._data = json.load(fh)

        city_location = {}
        for item in self._data:
            city = item['name']
            latitude = item['latitude']
            longitude = item['longitude']
            city_location[city] = (latitude, longitude)
        return city_location

class DisplayWindow(tk.Toplevel):
    '''The DisplayWindow displays the weathere data for each city.'''
    def __init__(self, master, city, data):
        super().__init__(master)
        self.master = master 

        self.title("City Weather")
        tk.Label(self, text=f"Weather for {city}", fg="blue").grid(column=0, row=0) 
        self.geometry("450x200")
        self.weather_data = '' 
        self.dates = data['time']
        self.max_temps = data['temperature_2m_max']
        self.min_temps = data['temperature_2m_min']
        self.uv = data['uv_index_max']
        self.wind_speed = data['wind_speed_10m_max']

        self.weather_data = city + ':\n' + ','.join(self.dates) + '\n' + ','.join(map(str, self.max_temps)) + '\n' + ','.join(map(str, self.wind_speed)) + '\n' + ','.join(map(str, self.uv)) + '\n' + ','.join(map(str, self.uv))
        self.master.get_selected_data().add(self.weather_data)

        frame = tk.Frame(self)
        tk.Label(frame, text='Date', fg="blue").grid(column=0, row=1)
        self.LB = tk.Listbox(frame, height=5, width=15)
        self.LB.grid(column=0, row=2) 
        for date in self.dates:
            self.LB.insert(tk.END, date)

        tk.Label(frame, text='High', fg="blue").grid(column=1, row=1)
        self.LB2 = tk.Listbox(frame, height=5, width=5)
        self.LB2.grid(column=1, row=2)
        for temp in self.max_temps:            
            self.LB2.insert(tk.END, temp)

        tk.Label(frame, text='Low', fg="blue").grid(column=2, row=1)
        self.LB3 = tk.Listbox(frame, height=5, width=5)
        self.LB3.grid(column=2, row=2)
        for temp in self.min_temps:            
            self.LB3.insert(tk.END, temp)
        
        tk.Label(frame, text='Wind', fg="blue").grid(column=3, row=1)
        self.LB4 = tk.Listbox(frame, height=5, width=5)
        self.LB4.grid(column=3, row=2)
        for temp in self.wind_speed:            
            self.LB4.insert(tk.END, temp)

        tk.Label(frame, text='UV', fg="blue").grid(column=4, row=1)
        self.LB4 = tk.Listbox(frame, height=5, width=5)
        self.LB4.grid(column=4, row=2)
        for uv in self.uv:            
            self.LB4.insert(tk.END, uv)

        frame.grid()
        self.grab_set() # disable event for other windows
        self.focus_set() # set focus on current window
        
def main():
    win1 = MainWindow()
    win1.mainloop() 

if __name__ == "__main__":
    main()

'''
              serial multithreading multiprocessing
geocoding      5.90      0.92            2.01
weather data   5.88      0.94            1.48

Serial > Multiprocessing  > Multithreading
- Multithreading was faster than multiprocessing because multithreading is best suited for IO bound operations (our case).
Multiprocessing is memory expensive, particularly with the Pool/mp.Queue as each process needs to pickle/unpickle data. The payoff 
would only be worth it in CPU bound operations
- Multiprocessing on it's own is faster than Serial since it utilizes 5 Cores at once in my program
'''
