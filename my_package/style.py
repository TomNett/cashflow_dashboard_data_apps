import streamlit as st
css_style = """
<style>
     .custom-column {
        margin: 20px;
    }

    
    .subheader {
        font-size: 24px;
        font-weight: bold;
        margin-top: 50px;
        margin-bottom:50px
    }

    .subheader-2 {
        font-size: 21px;
        font-weight: bold;
        margin-top: 50px;
        margin-bottom:50px
    }


// UPPER METRIC //
    .div-container{
    display: flex;
    margin: 10px
    background-color: #F9F9F9;

}
.div-icon{
    border-radius: 50%;
    width: 100px;
    height:100px; 
     flex-shrink: 0;
    background-color: #3CA0FF;
    display: flex;
    justify-content: center;
    align-items: center;
    margin-right: 1%;
}

.icon-img{
    max-width: 50%;
    max-height: 50%;
    float: left

}

.header{
    font-size: 15px;

}

.text{
    font-size: 26px;
    font-weight: bold;
    line-height: 2px;

}

.container {
  text-align: center;
  position: relative;
}

.container p {
  position: relative;
  z-index: 2;
}

.container img {
  position: relative;
  top: 20px; /* Adjust this value as needed */
  right: 5px
}


.centered-columns {
    display: flex;
    justify-content: center;
}



</style>
"""
def apply_css():
    css = """
    /* Base styles for light theme */
    body {
        font-family: Arial, sans-serif;
        color: #231F33;  /* Default text color */
    }

    /* Expander header */
    div[data-testid="stExpander"] div[role="button"] {
        
        border: 1px solid #ddd;
        padding: 10px 15px;
        border-radius: 4px;
        box-shadow: 0px 1px 3px rgba(0, 0, 0, 0.1);
        transition: background-color 0.3s ease;
    }

    /* Expander header text */
    div[data-testid="stExpander"] div[role="button"] p {
        font-size: 1.5rem;
        margin: 0;
        font-weight: 500;
    }

    /* Hover effect for expander header */
    div[data-testid="stExpander"] div[role="button"]:hover {
        background-color: #eaeaea;
    }

    /* Expander content */
    div[data-testid="stExpander"] div[data-baseweb="collapse"] {
        border: 1px solid #ddd;
        border-top: none;
        padding: 15px;
        
    }
    .stForm button {
        background-color: #4CAF50; /* Green background */
        border: none; /* Remove border */
        color: white; /* White text */
        padding: 15px 32px; /* Some padding */
        text-align: center; 
        text-decoration: none; 
        display: inline-block;
        font-size: 16px;
        margin: 4px 2px; 
        cursor: pointer; 
        border-radius: 4px; /* Rounded corners */
        transition-duration: 0.4s; /* Transition effect */
    }

    .stForm button:hover {
        background-color: #45a049; /* Darker green on hover */
    }
    """
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)