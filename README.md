# python-yacc-class-model
This is python-yacc class model. The rationale and usage is similar to python-yacc-function-model, and also similar to python-yacc.

## Structure of the File
The file *xparser.py* contains an abstract basic class called Parser. The constructor takes in a token string. The base class has two abstract methods, *pre* and *parse* that subclasses must implement.

## Usage
* You need to make two copies of the file *xparser.py*. 
* You use one copy to process the yacc spec files you write for parsing texts of your language. For each yacc spec file, it generates codes that you use in each pass. 
* You use another copy of *xparse.py* as the model of your own parser. Delete the two subclasses, and replace with your own subclasses. Each subclass is a *pass* you use to process your language.
* In each subclass you create, you copy and paste the codes generated from another copy. You must also implement the the abstract methods *pre* and *parse*. In *pre* you write any undefined terms in your yacc spec file. In *parse* you write some post processing codes.

## Notes
* The class model is good for separation of code components. But functions must use a lot of *self* which is very cumbersome.

