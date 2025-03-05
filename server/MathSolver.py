from pix2text import Pix2Text
from sympy.parsing.latex import parse_latex
import sympy as sp
from sympy import solveset, Eq, diff,Derivative
import tempfile
import os
sp.init_printing() 

class MathSolver:
    def __init__(self):
        self.p2t = Pix2Text.from_config()
    
    def save_image_to_temp(self, image):
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
        try:
            image.save(temp_file.name)
        except Exception as e:
            print(f"Error: Could not save image to temp file: {e}")
            os.remove(temp_file.name)
            return None
        finally:
            temp_file.close()
        return temp_file.name
    
    def extract_latex_from_image(self, image_path):
        """Extract LaTeX from image using Pix2Text"""
        try:
            latex_text = self.p2t.recognize(
                image_path, 
                file_type='text_formula', 
                return_text=True, 
                auto_line_break=False
            )
            # Clean up the latex text
            latex_text = latex_text.replace("$", "").strip()
            return latex_text
        except Exception as e:
            print(f"Error extracting LaTeX: {e}")
            raise
    
    def parse_latex(self, latex_text):
        """Parse LaTeX to SymPy expression"""
        try:
            # Handle escaped backslashes
            unescaped_latex = latex_text.replace("\\\\", "\\")
            return parse_latex(unescaped_latex)
        except Exception as e:
            print(f"Error parsing LaTeX: {e}\nLaTeX: {latex_text}")
            raise
    
    def detect_operation_type(self, latex_text):
        """Detect whether the expression is for solving, differentiation, or integration"""
        # Common integration symbols in LaTeX
        integration_patterns = [r"\int", r"\\int"]
        # Common differentiation symbols in LaTeX
        differentiation_patterns = [r"\frac{d}{d", r"\frac{\partial}{\partial", r"d/d", r"\partial/\partial"]
        
        # Check for integration
        for pattern in integration_patterns:
            if pattern in latex_text:
                return "integration"
        
        # Check for differentiation
        for pattern in differentiation_patterns:
            if pattern in latex_text:
                return "differentiation"
        
        # Check for equation
        if "=" in latex_text:
            return "equation"
        
        # Default to expression
        return "expression"
    
    def solve_equation(self, latex_text):
        """Solve an equation with an equals sign"""
        try:
            left_side, right_side = latex_text.split("=", 1)
            
            # Parse both sides
            left_expr = self.parse_latex(left_side.strip())
            right_expr = self.parse_latex(right_side.strip())
            
            # Create an equation
            equation = Eq(left_expr, right_expr)
            
            # Find all symbols in the equation
            all_symbols = equation.free_symbols
            
            if not all_symbols:
                # No variables to solve for, just return the expression
                return {
                    "type": "equation_without_variables",
                    "latex": latex_text,
                    "expression": str(equation),
                    "result": str(sp.simplify(left_expr - right_expr) == 0)
                }
            else:
                # Try to solve for each variable
                results = {}
                for var in all_symbols:
                    try:
                        solutions = solveset(equation, var)
                        if solutions:
                            results[str(var)] = [str(sol) for sol in solutions]
                    except Exception as e:
                        results[str(var)] = f"Could not solve for {var}: {str(e)}"
                
                return {
                    "type": "equation",
                    "latex": latex_text,
                    "expression": str(equation),
                    "variables": [str(sym) for sym in all_symbols],
                    "solutions": results
                }
        except Exception as e:
            print(f"Error solving equation: {e}")
            return {"type": "error", "message": str(e), "latex": latex_text}
    
    def perform_integration(self, latex_text):
        """Perform integration on an expression"""
        try:
            # Parse the expression
            expr = self.parse_latex(latex_text)
            
            # Find all symbols in the expression
            all_symbols = expr.free_symbols
            
            if not all_symbols:
                # No variables to integrate with respect to
                return {
                    "type": "integration_error",
                    "message": "No variables found for integration",
                    "latex": latex_text
                }
            
            # Try to integrate with respect to each variable
            results = {}
            for var in all_symbols:
                try:
                    integration_result = expr.doit()
                    results[str(var)] = str(integration_result)
                except Exception as e:
                    results[str(var)] = f"Could not integrate with respect to {var}: {str(e)}"
            
            return {
                "type": "integration",
                "latex": latex_text,
                "expression": str(expr),
                "variables": [str(sym) for sym in all_symbols],
                "results": results
            }
        except Exception as e:
            print(f"Error performing integration: {e}")
            return {"type": "error", "message": str(e), "latex": latex_text}
    
    def perform_differentiation(self, latex_text):
        """Perform differentiation on an expression"""
        try:
            # hacky solution, d/dx is sometimes parsed as d/d\times  fixing it here
            latex_text.replace(r'\\times',"x")
            # Parse the expression
            expr = self.parse_latex(latex_text)
            
            # Find all symbols in the expression
            all_symbols = expr.free_symbols
            
            if not all_symbols:
                # No variables to differentiate with respect to
                return {
                    "type": "differentiation_error",
                    "message": "No variables found for differentiation",
                    "latex": latex_text
                }
            
            
            results = {}
            if isinstance(expr,Derivative):
                results[str(expr.variables[0])] = str(expr.doit())
            else:
                # Try to differentiate with respect to each variable
                for var in all_symbols:
                    try:
                        diff_result = diff(expr,var)
                        print('diff',diff_result)
                        results[str(var)] = str(diff_result)
                    except Exception as e:
                        results[str(var)] = f"Could not differentiate with respect to {var}: {str(e)}"
            
            return {
                "type": "differentiation",
                "latex": latex_text,
                "expression": str(expr),
                "variables": [str(sym) for sym in all_symbols],
                "results": results
            }
        except Exception as e:
            print(f"Error performing differentiation: {e}")
            return {"type": "error", "message": str(e), "latex": latex_text}
    
    def simplify_expression(self, latex_text):
        """Simplify a mathematical expression"""
        try:
            expr = self.parse_latex(latex_text)
            simplified = sp.simplify(expr)
            if str(simplified) == str(expr):
                simplified = sp.expand(expr)
            return {
                "type": "expression",
                "latex": latex_text,
                "original": str(expr),
                "simplified": str(simplified)
            }
        except Exception as e:
            print(f"Error simplifying expression: {e}")
            return {"type": "error", "message": str(e), "latex": latex_text}
    
    def process_expression(self, latex_text):
        """Process a single mathematical expression based on its type"""
        operation_type = self.detect_operation_type(latex_text)
        
        if operation_type == "equation":
            return self.solve_equation(latex_text)
        elif operation_type == "integration":
            return self.perform_integration(latex_text)
        elif operation_type == "differentiation":
            return self.perform_differentiation(latex_text)
        else:
            return self.simplify_expression(latex_text)
    
    def process_image(self, image_path):
        """Process image and solve any equations, integrals, or derivatives found"""
        try:
            # Extract LaTeX from image
            latex_text = self.extract_latex_from_image(image_path)
            print(f"Extracted LaTeX: {latex_text}")
            
            # Handle multiple expressions (split by line breaks)
            if "\n" in latex_text:
                expressions = latex_text.split("\n")
                results = [self.process_expression(expr) for expr in expressions if expr.strip()]
                return results
            else:
                return [self.process_expression(latex_text)]
        except Exception as e:
            print(f"Error processing image: {e}")
            raise
