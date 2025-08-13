import pandas as pd
import numpy as np
import re
import tkinter as tk
from tkinter import messagebox, filedialog
from nltk.sentiment.vader import SentimentIntensityAnalyzer
import nltk
import os
import csv
from googletrans import Translator
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from PIL import Image, ImageTk

nltk.download('vader_lexicon')
sia = SentimentIntensityAnalyzer()
translator = Translator()

profane_words = {"russia", "ukraine", "iran","war"}

def contains_profanity(comment):
    words = comment.lower().split()
    return any(word in profane_words for word in words)

def mask_profanity(comment):
    words = comment.split()
    masked_words = [word if word.lower() not in profane_words else '*' * len(word) for word in words]
    return ' '.join(masked_words)

def is_negative_comment(comment):
    sentiment_score = sia.polarity_scores(comment)['compound']
    return sentiment_score < 0

def get_sentiment_feedback(comment):
    sentiment_score = sia.polarity_scores(comment)['compound']
    if sentiment_score >= 0.05:
        return "Positive"
    elif sentiment_score <= -0.05:
        return "Negative"
    else:
        return "Neutral"

def mask_bad_comment(comment):
    masked_comment = mask_profanity(comment)
    if is_negative_comment(comment):
        return '*' * len(comment)
    return masked_comment

def analyze_multilingual_comment(comment):
    try:
        detected_lang = translator.detect(comment).lang
        if detected_lang != 'en':
            translated_comment = translator.translate(comment, src=detected_lang, dest='en').text
        else:
            translated_comment = comment

        masked_comment = mask_bad_comment(translated_comment)
        sentiment = get_sentiment_feedback(translated_comment)
        return masked_comment, sentiment, detected_lang
    except Exception as e:
        return "Error analyzing comment.", "Error", "Unknown"

def show_admin_panel():
    comment_history = []

    def on_submit_comment():
        current_comment = text_comment.get("1.0", tk.END).strip()
        if not current_comment:
            return

        masked_comment, feedback, detected_lang = analyze_multilingual_comment(current_comment)

        text_blurred.delete(1.0, tk.END)
        text_blurred.insert(tk.END, masked_comment)

        label_feedback.config(text=f"Sentiment: {feedback} | Language: {detected_lang}")

        comment_history.append((current_comment, masked_comment, detected_lang, feedback))
        update_comment_history()
        update_sentiment_graph()

        check_bad_comment_threshold()

    def update_comment_history():
        text_history.delete(1.0, tk.END)
        for original, masked, lang, sentiment in comment_history:
            text_history.insert(
                tk.END,
                f"Original: {original}\nMasked: {masked}\nLanguage: {lang}\n\n"
            )

    def save_history_to_file():
        file_path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text Files", "*.txt")])
        if file_path:
            with open(file_path, 'w') as file:
                for original, masked, lang, sentiment in comment_history:
                    file.write(f"Original: {original}\nMasked: {masked}\nLanguage: {lang}\nSentiment: {sentiment}\n\n")
            messagebox.showinfo("Success", f"Comment history saved to {file_path}")

    def toggle_theme():
        current_theme = root.cget("bg")
        new_theme = "black" if current_theme == "white" else "white"
        fg_color = "white" if new_theme == "black" else "black"
        root.config(bg=new_theme)
        for widget in root.winfo_children():
            widget.config(bg=new_theme, fg=fg_color)

    def check_bad_comment_threshold():
        negative_count = sum(1 for original, _, _, feedback in comment_history if feedback == "Negative")
        if negative_count >= 3:
            messagebox.showwarning("Warning", "You have typed multiple bad comments! you have been blocked for next 24hrs if you feel we are wrong kindly contact us support@cybertron7.in")

    def update_sentiment_graph():
        sentiments = [sia.polarity_scores(comment)['compound'] for comment, _, _, _ in comment_history]
        time_points = list(range(len(sentiments)))

        fig = Figure(figsize=(5, 2), dpi=100)
        ax = fig.add_subplot(111)
        ax.plot(time_points, sentiments, marker='o')
        ax.set_title("Sentiment Over Time")
        ax.set_xlabel("Comment Count")
        ax.set_ylabel("Sentiment Score")

        for widget in frame_graph.winfo_children():
            widget.destroy()

        canvas = FigureCanvasTkAgg(fig, master=frame_graph)
        canvas.draw()
        canvas.get_tk_widget().pack()

    def export_to_csv():
        file_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV Files", "*.csv")])
        if file_path:
            with open(file_path, 'w', newline='') as csvfile:
                csv_writer = csv.writer(csvfile)
                csv_writer.writerow(["Original Comment", "Masked Comment", "Language", "Sentiment"])
                for original, masked, lang, sentiment in comment_history:
                    csv_writer.writerow([original, masked, lang, sentiment])
            messagebox.showinfo("Success", f"Comment history exported to {file_path}")

    def auto_save_history():
        if comment_history:
            with open("auto_saved_history.txt", 'w') as file:
                for original, masked, lang, sentiment in comment_history:
                    file.write(f"Original: {original}\nMasked: {masked}\nLanguage: {lang}\nSentiment: {sentiment}\n\n")
        root.after(60000, auto_save_history)  

    root = tk.Tk()
    root.title("Cybertron7")
    root.geometry("1200x800")
    root.config(bg="white")

   
   
    logo_image = Image.open("black_logo.png")  
    logo_image = logo_image.resize((250, 250), Image.Resampling.LANCZOS)
    logo_photo = ImageTk.PhotoImage(logo_image)

    logo_label = tk.Label(root, image=logo_photo, bg="white")
    logo_label.pack(side="left", padx=10, pady=10)

    frame = tk.Frame(root, padx=20, pady=20, bg="white")
    frame.pack()

    label_comment = tk.Label(frame, text="Type a Comment:", anchor="w", bg="white", fg="black")
    label_comment.grid(row=0, column=0, sticky="w")
    text_comment = tk.Text(frame, height=3, width=60, wrap='word')
    text_comment.grid(row=1, column=0, columnspan=2)

    label_blurred = tk.Label(frame, text="Blurred Comment (Masked):", anchor="w", bg="white", fg="black")
    label_blurred.grid(row=2, column=0, sticky="w")
    text_blurred = tk.Text(frame, height=3, width=60, wrap='word')
    text_blurred.grid(row=3, column=0, columnspan=2)

    label_feedback = tk.Label(frame, text="Sentiment: Neutral | Language: Unknown", anchor="w", bg="white", fg="black")
    label_feedback.grid(row=4, column=0, sticky="w")

    label_history = tk.Label(frame, text="Comment History:", anchor="w", bg="white", fg="black")
    label_history.grid(row=5, column=0, sticky="w")
    text_history = tk.Text(frame, height=10, width=60, wrap='word')
    text_history.grid(row=6, column=0, columnspan=2)

    btn_submit = tk.Button(frame, text="Submit Comment", command=on_submit_comment, bg="white", fg="black")
    btn_submit.grid(row=1, column=2)

    btn_save = tk.Button(frame, text="Save Comment History", command=save_history_to_file, bg="white", fg="black")
    btn_save.grid(row=7, column=0)

    btn_export = tk.Button(frame, text="Export to CSV", command=export_to_csv, bg="white", fg="black")
    btn_export.grid(row=7, column=1)

    btn_toggle_theme = tk.Button(frame, text="Toggle Theme", command=toggle_theme, bg="white", fg="black")
    btn_toggle_theme.grid(row=7, column=2)
    
    btn_exit = tk.Button(frame, text="Exit", command=root.destroy, bg="white",
                         fg="black")
    btn_exit.grid(row=7,column=5)
    

    frame_graph = tk.Frame(root)
    frame_graph.pack()

   
    footer = tk.Label(root, text="Cybertron7", bg="white", fg="black", font=("Arial", 18))
    footer.pack(side="bottom", pady=50)

    auto_save_history()
    root.mainloop()

show_admin_panel()
