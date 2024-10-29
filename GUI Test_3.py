from flask import Flask, render_template, request, send_file
import os
import zipfile
import re

app = Flask(__name__)

# Ensure the folder exists
output_folder = r"C:\Users\004DVP744\Documents\UKRI Docs\BIP Keyword Finder\Script"
os.makedirs(output_folder, exist_ok=True)

# Function to search keyword and permissions in xdoz and SEC files within xdoz folders
def search_keyword_in_xdoz_and_sec(parent_folder, keyword, output_file):
    with open(output_file, 'w', encoding='utf-8') as report:
        report.write("File Path, RoleDisplayName, Path, Permissions\n")
        found_any = False  # Flag to check if we found any results
        for root, dirs, files in os.walk(parent_folder):
            for file in files:
                if file.endswith(".xdoz"):
                    xdoz_file_path = os.path.join(root, file)
                    unzip_folder = os.path.join(root, file.replace(".xdoz", ""))
                    os.makedirs(unzip_folder, exist_ok=True)
                    with zipfile.ZipFile(xdoz_file_path, 'r') as zip_ref:
                        zip_ref.extractall(unzip_folder)
                    for dirpath, _, unzipped_files in os.walk(unzip_folder):
                        for unzipped_file in unzipped_files:
                            # Check for both .xdm and .sec files within the .xdoz folders
                            if unzipped_file.endswith(".xdo") or unzipped_file.endswith(".sec"):
                                file_path = os.path.join(dirpath, unzipped_file)
                                with open(file_path, 'r', encoding='utf-8') as f:
                                    content = f.read()
                                    if re.search(keyword, content, re.IGNORECASE):
                                        policies = re.findall(r'<policy.*?roleDisplayName="(.*?)".*?>(.*?)</policy>', content, re.IGNORECASE | re.DOTALL)
                                        for role_display_name, policy_content in policies:
                                            if re.search(keyword, role_display_name, re.IGNORECASE):
                                                permissions_matches = re.findall(r'<folderPermission>.*?<allow path="(.*?)".*?permissions="(.*?)".*?/>.*?</folderPermission>', policy_content, re.IGNORECASE | re.DOTALL)
                                                for path, permissions in permissions_matches:
                                                    permissions_clean = " | ".join([perm.split('.')[-1].capitalize() for perm in permissions.split(',;&#x9;') if perm.strip()])
                                                    report.write(f"{file_path}, {role_display_name}, {path}, {permissions_clean}\n")
                                                    found_any = True  # Mark that we found a result
        if not found_any:
            print("No results found for the given keyword.")
    return output_file

# Route for the home page
@app.route('/')
def home():
    return render_template('index4.html')

# Route for handling the form submission
@app.route('/search', methods=['POST'])
def search():
    # Get data from the form
    folder_path = request.form['folder']
    keyword = request.form['keyword']
    if not folder_path or not keyword:
        return "Please provide both the folder path and the keyword."
    output_file = os.path.join(output_folder, "keyword_search_report.csv")  # Update to use the correct path
    print(f"Searching in folder: {folder_path} for keyword: '{keyword}'")
    # Run the search function
    result_file = search_keyword_in_xdoz_and_sec(folder_path, keyword, output_file)
    return send_file(result_file, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=5000)
