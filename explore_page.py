import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt


def shorten_categories(categories, cutoff):
    categorical_map = {}
    for i in range(len(categories)):
        if categories .values[i] >= cutoff:
            categorical_map[categories.index[i]] = categories.index[i]
        else:
            categorical_map[categories.index[i]] = "other"
    return categorical_map


def clean_experience(x):
    if x == "More than 50 years":
        return 50
    if x == "Less than 1 year":
        return 0.5
    return float(x)



def clean_education(x):
   
     if "Bachelor’s degree" in x:
        return "Bachelor’s degree"
     if "Master’s degree" in x:
        return "Master’s degree"
     if "Professional degree" in x or "Other doctoral" in x:
        return "Post grad"
     return "less than a Bachelor’s"
   


def clean_employment(x):
    if x == "Employed full-time":
        return "full-time"
    elif x == "Employed part-time":
        return "part-time"



def clean_undergrad_major(x):
    if pd.isnull(x):
        return "Unknown"
    
    x = x.lower()  # make lowercase for easier matching
    
    if "computer science" in x or "software engineering" in x or "computer engineering" in x:
        return "CS/Software Eng"
    elif "information systems" in x or "information technology" in x or "system administration" in x:
        return "IT/Systems"
    elif "engineering" in x:
        return "Other Engineering"
    elif "natural science" in x:
        return "Natural Sciences"
    elif "web development" in x or "web design" in x:
        return "Web Dev/Design"
    elif "mathematics" in x or "statistics" in x:
        return "Math/Stats"
    elif "business" in x:
        return "Business"
    elif "humanities" in x:
        return "Humanities"
    elif "social science" in x:
        return "Social Sciences"
    elif "fine arts" in x or "performing arts" in x:
        return "Arts"
    elif "never declared" in x:
        return "Undeclared"
    elif "health science" in x:
        return "Health Sciences"
    else:
        return "Other"  # catch any unusual entries
    
def shorten_categories(categories, cutoff):
     categorical_map = {}
     for i in range(len(categories)):
        if categories .values[i] >= cutoff:
            categorical_map[categories.index[i]] = categories.index[i]
        else:
            categorical_map[categories.index[i]] = "other"
     return categorical_map


@st.cache_data
def load_data():
    df = pd.read_csv("data/survey_results_public.csv")

    df = df[[
        "Country",
        "EdLevel",
        "YearsCodePro",
        "Employment",
        "WebframeWorkedWith",
        "UndergradMajor",
        "ConvertedComp"
    ]]

    # rename once, immediately
    df = df.rename(columns={
        "ConvertedComp": "Salary",
        "YearsCodePro": "Experience"
    })

    # now these columns exist
    df = df[df["Salary"].notnull()]
    df = df.dropna()

    df["Experience"] = df["Experience"].apply(clean_experience)

    df["Employment"] = df["Employment"].map({
        "Employed full-time": "full-time",
        "Employed part-time": "part-time"
    }).fillna("other")

    country_map = shorten_categories(df["Country"].value_counts(), 400)
    df["Country"] = df["Country"].map(country_map)

    web_map = shorten_categories(df["WebframeWorkedWith"].value_counts(), 400)
    df["WebframeWorkedWith"] = df["WebframeWorkedWith"].map(web_map)

    df["UndergradMajor"] = df["UndergradMajor"].apply(clean_undergrad_major)
    df["EdLevel"] = df["EdLevel"].apply(clean_education)

    df = df[(df["Salary"] >= 10_000) & (df["Salary"] <= 250_000)]

    return df

#loading the data
df = load_data()
def show_explore_page():
    
    st.title("Explore Software Developer Salaries")

    st.write(
        """
    ### Stack Overflow Developer Survey 2020
    """
    )

    st.write(
        """
    This page is for exploring the data used to build the salary prediction model.
    """
    )

    data = df["Country"].value_counts()

    fig1,ax1 = plt.subplots()
    ax1.pie(data,labels=data.index,autopct="%1.1f%%",shadow=True, startangle=90)#arguements to get a nicer look
    ax1.axis("equal")#equal aspect ratio tat ensures that pie is drawn as a circle
    
    st.write("""###Number of data from different countries""")
    
    st.pyplot(fig1)



    st.write(
        """
    ### Mean Salary based on Country
    """
    )

    data = df.groupby(["Country"])["Salary"].mean().sort_values(ascending=True)
    st.bar_chart(data)

    st.write(
        """### Mean Salary based on Experience
    """
    )

    data = df.groupby(["Experience"])["Salary"].mean().sort_values(ascending=True)
    st.line_chart(data)
