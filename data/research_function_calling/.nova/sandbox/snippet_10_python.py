# Define a function to call a tool
def call_tool(tool_name, input_data):
    try:
        # Invoke the tool using the input data
        result = tool_name.invoke(input_data)
        return result
    except Exception as e:
        # Catch any exceptions raised during function calling
        print(f"Error calling tool: {e}")
        return None

# Use the function to call a tool
result = call_tool("example_tool", "input_data")

# Process the result
if result:
    print("Tool called successfully")
else:
    print("Error calling tool")