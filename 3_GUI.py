import io
import tkinter as tk
from tkinter import messagebox, filedialog, simpledialog
from PIL import Image, ImageTk
import requests
import csv
import pandas as pd
from requests_html import HTMLSession

class WebImageClassifierApp:
    def __init__(self, root, csv_path):
        self.root = root
        self.root.title("Web Image Classifier")
        self.session = HTMLSession()

        self.csv_path = csv_path

        # Read the CSV
        self.df = pd.read_csv(self.csv_path, encoding='latin1')
        self.df.to_csv("backup.csv", encoding='latin1')
        self.pages = self.df['urls'].tolist()
        self.categories = self.df['word'].tolist()
        if 'categorization' in self.df.columns:
            self.categorization = self.df['categorization'].tolist()
        else:
            self.categorization = [None] * len(self.df)
        self.current_page_index = 0

        self.max_width = 500
        self.max_height = 700

        # Configure GUI
        self.setup_gui()

        # Show first page
        self.load_page()

    def setup_gui(self):


        # Frame for navigation and categorization
        nav_frame = tk.Frame(self.root)
        nav_frame.pack(padx=10, pady=10)

        # Navigation buttons
        self.prev_button = tk.Button(nav_frame, text="Previous", command=self.prev_image)
        self.prev_button.pack(side=tk.LEFT, padx=10)

        self.next_button = tk.Button(nav_frame, text="Next", command=self.next_image)
        self.next_button.pack(side=tk.LEFT, padx=10)

        # Entry for page number
        self.page_entry_label = tk.Label(nav_frame, text="Go to image:")
        self.page_entry_label.pack(side=tk.LEFT, padx=10)

        self.page_entry = tk.Entry(nav_frame, width=5)
        self.page_entry.pack(side=tk.LEFT)

        self.go_to_button = tk.Button(nav_frame, text="Go", command=self.go_to_page)
        self.go_to_button.pack(side=tk.LEFT, padx=10)

        # Category label and categorization buttons
        self.category_label = tk.Label(self.root, text="Category:")
        self.category_label.pack(pady=5, anchor='w', side='top', fill='both')

        categorize_frame = tk.Frame(self.root)
        categorize_frame.pack(padx=10, pady=10)

        self.categorize_button_ok = tk.Button(categorize_frame, text="Good", command=self.categorize_image_ok, bg="#8AE996")
        self.categorize_button_ok.pack(side=tk.RIGHT, padx=10)

        self.categorize_button_bad = tk.Button(categorize_frame, text="Bad", command=self.categorize_image_bad, bg="#E99698")
        self.categorize_button_bad.pack(side=tk.LEFT, padx=10)

        # Frame for image and category
        self.image_frame = tk.Frame(self.root)
        self.image_frame.pack(padx=10, pady=10)

        self.image_label = tk.Label(self.image_frame, text="Image")
        self.image_label.pack(padx=10, pady=10)

        # Menu
        menu_bar = tk.Menu(self.root)
        self.root.config(menu=menu_bar)

        file_menu = tk.Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label="Archive", menu=file_menu)
        file_menu.add_command(label="Save CSV", command=self.save_csv)


    def resize_image(self, image, max_width, max_height):
        original_width, original_height = image.size
        ratio = min(max_width / original_width, max_height / original_height)
        new_width = int(original_width * ratio)
        new_height = int(original_height * ratio)
        return image.resize((new_width, new_height), Image.LANCZOS)

    def load_page(self):
        url = self.pages[self.current_page_index]

        response = requests.get(url)
        self.current_image = Image.open(io.BytesIO(response.content))

        self.current_image = self.resize_image(self.current_image, self.max_width, self.max_height)
        self.img_tk = ImageTk.PhotoImage(self.current_image)
        self.image_label.config(image=self.img_tk)

        # Show current category
        self.category_label.config(text=f"Category: {self.categories[self.current_page_index]}")

    def next_image(self):
        if self.current_page_index < len(self.pages) - 1:
            self.current_page_index += 1
            self.load_page()
        else:
            messagebox.showinfo("End of pages", "You have already reached the last page.")

    def prev_image(self):
        if self.current_page_index > 0:
            self.current_page_index -= 1
            self.load_page()
        else:
            messagebox.showinfo("Top of pages", "You are on the first page.")

    def go_to_page(self):
        try:
            page_number = int(self.page_entry.get()) - 1
            if 0 <= page_number < len(self.pages):
                self.current_page_index = page_number
                self.load_page()
            else:
                messagebox.showerror("Error", f"Page number out of range (1 - {len(self.pages)})")
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid page number.")
    def categorize_image_ok(self):
        
        self.categorization[self.current_page_index] = True
        self.next_image()

    def categorize_image_bad(self):
        
        self.categorization[self.current_page_index] = False
        self.next_image()
   

    def save_csv(self):

        self.df['categorization'] = self.categorization


      
        # Save the final CSV
        self.df.to_csv(self.csv_path, index=False, encoding='latin1')

        messagebox.showinfo("Saved", f"CSV file saved in {self.csv_path}")

# Initialize the application
root = tk.Tk()
app = WebImageClassifierApp(root, 'image_results.csv')
root.mainloop()