import pymupdf
import os
import json



def get_qp_info(paper_names, shortened_paper_names):

    folders = os.listdir()
    if "output" not in folders:
        os.mkdir("output")

    exam_paths = os.listdir("./exams")

    # looping through all exam PDFs
    for path in exam_paths:
        
        # Opening the exam PDF
        doc = pymupdf.open(f"./exams/{path}")
        page = doc[0]

        # Screenshot the exam details (not needed right now)
        # exam_details = page.get_pixmap(clip = fitz.Rect(112,131,525, 300))
        # date = page.get_pixmap(clip= fitz.Rect(116, 162, 500, 190))
        
        # Get the exam details
        full_date = page.get_textbox(pymupdf.Rect(116, 162, 500, 190))
        date = full_date.split() # DayName, Day, Month, Year
        session = date[2]
        year = date[3]
        session = session.lower()

         
        paper = None
        index = None

        # Find paper name from premade list
        for i,p in enumerate(paper_names):
            if page.search_for(p):
                paper = p
                index = i


        
        output_folder = f"{year}_{session}_{shortened_paper_names[index]}"
        # print(f"{path}-----{output_folder}")

        folders = os.listdir("./output")
        if output_folder not in folders:
            os.makedirs(f"./output/{output_folder}", exist_ok=True)
            os.mkdir(f"./output/{output_folder}/screenshots")


        output = {
            "exam":{
                "year": int(year),
                "session": session,
                "paper": paper
            },
            "questions": []
        }

        # Getting the total number of questions and each question's mark
        num_questions = 0
        marks = []
        for p in doc:
            n = p.search_for("Total for Question")
            if n:
                
                num_questions+=1
                clipped = n[0]           
                clipped.x1 += 30
                full_date = p.get_textbox(clipped)
                mark = full_date.split()[5]
                marks.append(mark)
                        

        q = []
        for i in range(1,num_questions + 1):
            q.append(i) # [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        
        i = 0
        # Later: make it so if a paper uses QNumber: instead of QNumber. it still detects it
        for p in doc:
            if i == num_questions:
                break
            
            st = p.search_for(f"{q[i]}.")
            # st2 = p.search_for(f"{q[i]}:")
            en = p.search_for(")")
            
            if st and en:
                i += 1
                st = st[0]
                en = en[-1]
                clipped = pymupdf.Rect(st.x0, st.y0, en.x1, en.y1)
                pix = p.get_pixmap(clip=clipped)
                img_path = f"./output/{output_folder}/screenshots/{output_folder}_q{i}.png"
                pix.save(img_path)    
                
                question_dict = {
                    "question_number": i,
                    "marks": int(marks[i-1]),
                    "image_path": img_path ,
                    # Write the paths that will be made by the get_ms_info function
                    "mark_scheme_path": [],
                    "checked": False
                }
                output["questions"].append(question_dict)

            # if st2 and en:
            #     i += 1
            #     st2 = st2[0]
            #     en = en[-1]
            #     clipped = pymupdf.Rect(st2.x0, st2.y0, en.x1, en.y1)
            #     pix = p.get_pixmap(clip=clipped)
            #     img_path = f"./output/{output_folder}/screenshots/{output_folder}_q{i}.png"
            #     pix.save(img_path)    
                
            #     question_dict = {
            #         "question_number": i,
            #         "marks": int(marks[i-1]),
            #         "image_path": img_path ,
            #     }
            #     output["questions"].append(question_dict)

            
        json_string = json.dumps(output)
        
        with open(f"./output/{output_folder}/{output_folder}.json", "w") as f:
            f.write(json_string)
        f.close()

        


def get_ms_info(paper_names, shortened_paper_names):


    markschemes = os.listdir("./mark_schemes")

    for path in markschemes:
        try:
            doc = pymupdf.open(f"./mark_schemes/{path}")
            
            
            page = doc[0]
            
            # Get the exam date to find the folder to save the ms in
            data = page.get_textbox(pymupdf.Rect(0, 307, 400, 345))

            
            
            data = data.split()
            session = data[0].lower()
            year = int(data[1])
            for i,p in enumerate(paper_names):
                if page.search_for(p):
                    paper = p
                    index = i
            
            exam_folder_path = f"{year}_{session}_{shortened_paper_names[index]}"


            folder_to_save_in = f"./output/{exam_folder_path}"

            folders = os.listdir(folder_to_save_in)
            if "ms_screenshots" not in folders:
                os.mkdir(f"{folder_to_save_in}/ms_screenshots")
            
            
            folder_to_save_in = f"{folder_to_save_in}/ms_screenshots"
            
            # Counting How many questions exist
            question_location = []
            for idx, page in enumerate(doc):
                text = page.search_for("Number Scheme")
                if text and text[0].y0 < 300:
                    question_location.append(idx)

            # print(question_location) # [6,8,9,12,14,16,18,21,24,27]
            # Creating a folder for each question (to store answers in)
            # for idx, question_page in enumerate(question_location):
            #     if f"question{idx+1}" not in folders:
            #         os.mkdir(f"{folder_to_save_in}/question{idx+1}")
            
            pages_per_q =  []
            folders = os.listdir(folder_to_save_in)
            question_number = 1
            
            # Finding how many pages does each individual question's ms have.
            for idx, question_page in enumerate(question_location):
                q_name = f"question{idx+1}"
                q_folder_path = f"{folder_to_save_in}/{q_name}"

                if q_name not in folders:
                    os.mkdir(q_folder_path)

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
            
            # Editing JSON to link to the page images directly
            with open(f"./output/{exam_folder_path}/{exam_folder_path}.json", "r+") as f:
                py_dict = json.load(f)

            

            for idx, question in enumerate(py_dict["questions"]):
                for i in range(1, pages_per_q[idx]):
                    question["mark_scheme_path"].append(f"{folder_to_save_in}/question{idx+1}/page{i}")

        except FileNotFoundError:
            print(path)
            continue

    json_string = json.dumps(py_dict)
        
    with open(f"./output/{exam_folder_path}/{exam_folder_path}.json", "w") as f:
        f.write(json_string)
    f.close()


paper_names = ["Pure Mathematics P1", "Pure Mathematics P2", "Pure Mathematics P3", "Pure Mathematics P4"]
shortened_paper_names = ["pm1", "pm2", "pm3", "pm4"]

get_qp_info(paper_names, shortened_paper_names)
get_ms_info(paper_names, shortened_paper_names)







