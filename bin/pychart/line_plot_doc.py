# automatically generated by generate_docs.py.
doc="""Attributes supported by this class are:
y_qerror_minus_col(type:int) default="<<error_bar>>".
xcol(type:int) default="The column, within attribute "data", from which the X values of sample points are extracted. <<chart_data>>".
error_bar(type:error_bar.T) default="The style of the error bar. <<error_bar>>".
data_label_format(type:printf format string) default="The format string for the label printed 
                          beside a sample point.
                          It can be a `printf' style format string, or 
                          a two-parameter function that takes the (x, y)
                          values and returns a string. The appearance of the string produced here can be
controlled using escape sequences. <<font>>".
ycol(type:int) default="The column, within attribute "data", from which the Y values of sample points are extracted. <<chart_data>>".
label(type:str) default="The label to be displayed in the legend. <<legend>>, <<font>>".
line_style(type:line_style.T) default="The style of the line. ".
    By default, a style is picked from standard styles round-robin.
    See also pychart.line_style
    
y_error_plus_col(type:int) default="The column (within "data") from which the height of the errorbar is extracted. Meaningful only when error_bar != None. <<error_bar>>".
tick_mark(type:tick_mark.T) default="Tick marks to be displayed at each sample point. <<tick_mark>>".
y_error_minus_col(type:int) default="The column (within "data") from which the depth of the errorbar is extracted. Meaningful only when error_bar != None. <<error_bar>>".
data_label_offset(type:(x,y)) default="The location of data labels relative to the sample point. Meaningful only when data_label_format != None.".
data(type:any) default="Specifies the data points. <<chart_data>>".
y_qerror_plus_col(type:int) default="<<error_bar>>".
"""

