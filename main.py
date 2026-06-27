import pymupdf
import os
import json
import re

paper_names = ["Pure Mathematics P1", "Pure Mathematics P2", "Pure Mathematics P3", "Pure Mathematics P4"]
shortened_paper_names = ["pm1", "pm2", "pm3", "pm4"]
short_paper_names = ["p1","p2","p3","p4"]

paper_codes = ["WMA11", "WMA12", "WMA13", "WMA14"]

session_names = ["january", "may"]
short_session_names = ["jan", "may"]

file_name_pattern = rf"^\d{{4}}_({'|'.join(session_names)})_({'|'.join(shortened_paper_names)})$"


qp_pdfs_path = "./exams"
ms_pdfs_path = "./mark_schemes"

log_file = "errors.txt"

err_amount = 0
no_of_pdfs = max(len(os.listdir(qp_pdfs_path)), len(os.listdir(ms_pdfs_path)))


# Create needed folders and files
def folder_setup():
    global err_amount

    os.makedirs("output", exist_ok=True)
    
    # Generate error folders
    os.makedirs("errors/qp/duplicates", exist_ok=True)
    os.makedirs("errors/qp/data_not_found", exist_ok=True)
    os.makedirs("errors/qp/corrosponding", exist_ok=True)

    os.makedirs("errors/ms/duplicates", exist_ok=True)
    os.makedirs("errors/ms/data_not_found", exist_ok=True)
    os.makedirs("errors/ms/corrosponding", exist_ok=True)

    os.makedirs("errors/question_amount/", exist_ok=True)

    files = []
    ms_files = os.listdir(ms_pdfs_path)
    qp_files = os.listdir(qp_pdfs_path)
    
    # Check if a qp file has a corrosponding ms file and vice-versa
    for p in qp_files:
        if p not in ms_files:
            os.rename(f"{qp_pdfs_path}/{p}",f"./errors/qp/corrosponding/{p}")
            err_amount += 1
            with open(log_file, "a") as f:
                f.write(f"Corrosponding File Not Found: {qp_pdfs_path}/{p} --> errors/qp/corrosponding/{p}\n")

    for p in ms_files:
        if p not in qp_files:
            os.rename(f"{ms_pdfs_path}/{p}",f"./errors/ms/corrosponding/{p}")
            err_amount += 1
            with open(log_file, "a") as f:
                f.write(f"Corrosponding File Not Found: {ms_pdfs_path}/{p} --> errors/ms/corrosponding/{p}\n")


    # Create the necessary folders for files that passed
    for p in os.listdir(qp_pdfs_path):
        file_name = os.path.splitext(p)[0]
        os.makedirs(f"./output/{file_name}/qp_screenshots", exist_ok=True)
        os.makedirs(f"./output/{file_name}/ms_screenshots", exist_ok=True)

# Find year, session, paper name. Then change file name
def check_qp(): 
    global err_amount
    cnt = 0
    dup = 0
    for path in os.listdir(qp_pdfs_path):
        file_name = os.path.splitext(path)[0]

        # If the names are already done skip
        if re.match(file_name_pattern, file_name):
            continue

        original_path = f"{qp_pdfs_path}/{path}"
        path = path.lower()
        session = None
        paper_name = None
        year = None

        # Finding data through the file name
        for s in session_names:
            s = s.lower()
            if path.find(s) >= 0:
                session = s
                break
        

        for p in shortened_paper_names:
            p = p.lower()
            if path.find(p) >= 0:
                paper_name = p
                break
        

        if not session:
            for idx, s in enumerate(short_session_names):
                s = s.lower()
                if path.find(s) >= 0:
                    session = session_names[idx]
                    break

        if not paper_name:
            for idx ,p in enumerate(short_paper_names):
                p = p.lower()
                if path.find(p) >= 0:
                    paper_name = shortened_paper_names[idx]
                    break
        
        # Finding data using the PDF
        doc = pymupdf.open(original_path)
        page = doc[0]
        text = page.get_text().lower()
        
        if not session:
            for s in session_names:
                pattern = rf"\b{s}\b\s*\d{{4}}"
                matches = re.findall(pattern, text)
                if matches:
                    session = s
                    break

        if not paper_name:
            for idx, p in enumerate(paper_names):
                p = p.lower()
                if text.find(p) >= 0:
                    paper_name = shortened_paper_names[idx]
                    break
         
        year = re.findall(r'\b\d{4}\b', text)[0]

        # If data is still not found
        if not session:
            session = "na"
        if not paper_name:
            paper_name = "na"
        if not year:
            year = f"na"

        

        exam = f"{year}_{session}_{paper_name}"
        

        try:
            if exam.find("na") != -1:
                cnt += 1 
                os.rename(original_path, f"errors/qp/data_not_found/{exam}_{cnt}.pdf")
                with open(log_file, "a") as f:
                    err_amount += 1
                    f.write(f"DataNotFound: {original_path} --> errors/qp/data_not_found/{exam}_{cnt}.pdf\n")
                
            else:
                os.rename(original_path, f"{qp_pdfs_path}/{exam}.pdf")
        
        except FileExistsError:
            os.rename(original_path, f"errors/qp/duplicates/{exam}_{dup}.pdf")
            with open(log_file, "a") as f:
                err_amount += 1
                f.write(f"FileExistsError: {original_path} --> errors/qp/duplicates/{exam}_{dup}.pdf\n")
            dup += 1

# Screenshot each question in each qp and then setup json file to link screenshots with known data (question number, amount of marks in the question)
def get_qp_info(): 
    global err_amount

    for path in os.listdir(qp_pdfs_path):
        file_name = os.path.splitext(path)[0]
        data = file_name.split("_") # [year, session, paper]
        # Find long paper name
        for idx, name in enumerate(shortened_paper_names):
            if name == data[2]:
                data[2] = paper_names[idx]


        output = {
            "exam":{
                "year": int(data[0]),
                "session": data[1],
                "paper": data[2]
            },
            "questions": []
        }

        # Getting the total number of questions and each question's mark
        doc = pymupdf.open(f"{qp_pdfs_path}/{path}")
        
        full_text = ""
        for page in doc[1:]:
            full_text += page.get_text()
        pattern = r"(\d+)\s*(mark|marks)"
        matches = re.findall(pattern, full_text, flags=re.IGNORECASE)
        
        marks = []
        for t in matches:
            mark = int(t[0])
            if mark <= 20:
                marks.append(mark)
        num_questions = len(marks)
        
                        
        # Screenshot each question
        q = []
        for no_screenshots in range(1,num_questions + 1):
            q.append(no_screenshots) # [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        
        
        check = False 
        p_num = 0
        no_screenshots = 0
        while p_num < len(doc):
            p = doc[p_num]
            if no_screenshots == num_questions:
                break
            
            # Method 1 (e.g. "1.")
            st = p.search_for(f"{q[no_screenshots]}.")

            if p_num == len(doc) - 2 and no_screenshots <= 5 and check == False: # Got 5 screenshots in that exam (probably didnt get all the questions) so switch to method 2:
                check = True
                p_num = 0
                no_screenshots = 0
            
            # Method 2 (e.g. "1:")
            if check == True:
                st = p.search_for(f"{q[no_screenshots]}:")
            

            en = p.search_for(")")
            if st and en:
                no_screenshots += 1
                st = st[0]
                en = en[-1]
                clipped = pymupdf.Rect(st.x0, st.y0, en.x1, en.y1)
                pix = p.get_pixmap(clip=clipped)
                img_path = f"./output/{file_name}/qp_screenshots/{file_name}_q{no_screenshots}.png"
                pix.save(img_path)    
                
                question_dict = {
                    "question_number": no_screenshots,
                    "marks": int(marks[no_screenshots-1]),
                    "image_path": img_path ,
                    "mark_scheme_path": [],
                    "checked": False
                }
                output["questions"].append(question_dict)
            p_num += 1
    
        json_string = json.dumps(output)
        
        with open(f"./output/{file_name}/{file_name}.json", "w") as f:
            f.write(json_string)
        f.close()


# Find year, session, paper name from ms pdf. Then change file name
def check_ms():
    global err_amount
    cnt = 0
    dup = 0
    for path in os.listdir(ms_pdfs_path):

        file_name = os.path.splitext(path)[0]
        # If the names are already done skip
        if re.match(file_name_pattern, file_name):
            continue

        original_path = f"{ms_pdfs_path}/{path}"
        path = path.lower()
        session = None
        paper_name = None
        year = None

        # Finding data through the file name
        for s in session_names:
            s = s.lower()
            if path.find(s) >= 0:
                session = s
                break
        

        for p in shortened_paper_names:
            p = p.lower()
            if path.find(p) >= 0:
                paper_name = p
                break
        

        if not session:
            for idx,s in enumerate(short_session_names):
                s = s.lower()
                if path.find(s) >= 0:
                    session = session_names[idx]
                    break

        if not paper_name:
            for idx ,p in enumerate(short_paper_names):
                p = p.lower()
                if path.find(p) >= 0:
                    paper_name = shortened_paper_names[idx]
                    break
        
        # Finding data using the PDF
        doc = pymupdf.open(original_path)
        page = doc[0]
        text = page.get_text().lower()
        
        # hardcoded fix for now
        if not session:
            pattern = r"\bsummer\b"
            matches = re.findall(pattern, text, flags=re.IGNORECASE)
            if matches:
                session = "may"
                
                

        if not session:
            for s in session_names:
                pattern = rf"\b{s}\b\s*\d{{4}}"
                matches = re.findall(pattern, text)
                if matches:
                    session = s
                    break
        
        if not paper_name:
            for idx, s in enumerate(paper_codes):
                if text.find(s):
                    paper_name = shortened_paper_names[idx]
                    break

        if not paper_name:
            for idx, p in enumerate(paper_names):
                p = p.lower()
                if text.find(p) >= 0:
                    paper_name = shortened_paper_names[idx]
                    break
         
        year = re.findall(r'\b\d{4}\b', text)[0]

        # If data is still not found
        if not session:
            session = "na"
        if not paper_name:
            paper_name = "na"
        if not year:
            year = f"na"

        exam = f"{year}_{session}_{paper_name}"
        try:
            if exam.find("na") != -1:
                cnt += 1 
                os.rename(original_path, f"errors/ms/data_not_found/{exam}_{cnt}.pdf")
                with open(log_file, "a") as f:
                    err_amount += 1
                    f.write(f"DataNotFound: {original_path} --> errors/ms/data_not_found/{exam}_{cnt}.pdf\n")
                
            else:
                os.rename(original_path, f"{ms_pdfs_path}/{exam}.pdf")
        
        except FileExistsError:
            os.rename(original_path, f"errors/ms/duplicates/{exam}_{dup}.pdf")
            with open(log_file, "a") as f:
                err_amount += 1
                f.write(f"FileExistsError: {original_path} --> errors/ms/duplicates/{exam}_{dup}.pdf\n")
            dup += 1
    

def get_ms_info():
    global err_amount

    for path in os.listdir(ms_pdfs_path):
        doc = pymupdf.open(f"{ms_pdfs_path}/{path}")

        file_name = os.path.splitext(path)[0]
        data = file_name.split("_") # [year, session, paper]
        
        exam_folder_path = f"{data[0]}_{data[1]}_{data[2]}"

        folder_to_save_in = f"./output/{exam_folder_path}/ms_screenshots"

        
                
        # Counting How many questions exist and appending the page_number they are in
        
        question_location = []
        for idx, page in enumerate(doc):
            text = page.search_for("Number Scheme")
            if text and text[0].y0 < 300:
                question_location.append(idx)

        # print(question_location) # [6,8,9,12,14,16,18,21,24,27]
        pages_per_q =  []
        tables_per_q = []
        question_number = 1
        


        # Finding how many pages does each individual question's ms have.
        # Creating a folder for each question (to store answers in)
        for idx, question_page in enumerate(question_location):
            q_name = f"question{idx+1}"
            q_folder_path = f"{folder_to_save_in}/{q_name}"

            
            os.makedirs(f"{q_folder_path}/table", exist_ok=True)

            if idx + 1 < len(question_location):
                end_page = question_location[idx + 1]
            else:
                end_page = len(doc)-1
        
            page_number = 1
            
            # Each question could have multiple pages in its mark scheme
            # Saving each page in its question's folder
            for j in range(question_page, end_page):
                page = doc[j]
                save_path = f"{q_folder_path}/page{page_number}.png"
                pix = page.get_pixmap(dpi=150)
                pix.save(save_path)
                    
                page_number += 1

                
            
            pages_per_q.append(page_number)

            question_number += 1
            table_number = 0
            for j in range(question_page, end_page):
                page = doc[j]
                tables = doc[j].find_tables()
                # print(j)
                if tables.tables:
                    tab = tables.tables[0]  # Select the first table
                    bbox = tab.bbox         # Get bounding box: (x0, y0, x1, y1)
                    
                    # Create a pixmap (image) of just the table area
                    pix = page.get_pixmap(clip=bbox)
                    
                    # Save as PNG
                    pix.save(f"{q_folder_path}/table/table{table_number}.png")
                    pix = None
                    table_number += 1
        
            tables_per_q.append(table_number)

            
        # Editing JSON to link to the page images directly
        with open(f"./output/{exam_folder_path}/{exam_folder_path}.json", "r+") as f:
            py_dict = json.load(f)

        # If the number of questions found in ms not equal the number of questions we got from qp
        if(len(pages_per_q) != len(py_dict["questions"])):
            os.makedirs(f"./errors/question_amount/{exam_folder_path}", exist_ok=True)
            os.rename(f"{ms_pdfs_path}/{exam_folder_path}.pdf", f"./errors/question_amount/{exam_folder_path}/{exam_folder_path}_ms.pdf")
            os.rename(f"{qp_pdfs_path}/{exam_folder_path}.pdf", f"./errors/question_amount/{exam_folder_path}/{exam_folder_path}_qp.pdf")
            os.rename(f"./output/{exam_folder_path}", f"./errors/question_amount/{exam_folder_path}/{exam_folder_path}")
            
            with open(log_file, "a") as f:
                err_amount += 1
                f.write(f"Question Amount Difference: ms: {len(pages_per_q)}, qp: {len(py_dict["questions"])} --> moved {exam_folder_path}\n")
            continue
        else:
            for idx, question in enumerate(py_dict["questions"]):
                question["mark_scheme_path"].append(f"{folder_to_save_in}/question{idx+1}/table/table0")

                for i in range(1, pages_per_q[idx]):
                    question["mark_scheme_path"].append(f"{folder_to_save_in}/question{idx+1}/page{i}")

        

        json_string = json.dumps(py_dict)
            
        with open(f"./output/{exam_folder_path}/{exam_folder_path}.json", "w") as f:
            f.write(json_string)
        f.close()






check_qp() 
check_ms() 
folder_setup() 




get_qp_info()
get_ms_info()

print(f"Error Percentage = {(err_amount/no_of_pdfs)*100}%")