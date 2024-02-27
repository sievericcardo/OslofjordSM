import requests
import logging
import json

class HasuraMutaion:
    def __init__(self):
        self.results = []
        self.hasura_url = "http://localhost:8080/v1/graphql"
        self.headers = {
            "Content-Type": "application/json",
            "x-hasura-admin-secret": "mylongsecretkey",
        }

    def data_for_muation(self, json_data):
        # Append the JSON data to the results list
        self.results.append(json.loads(json_data))


    def run_mutation(self): 
        # mutation MyMutation($objects: [simulations_insert_input!]!) {
        
        # GraphQL mutation with variables
        mutation_query = """
        mutation MyMutation($objects: [simulations_insert_input!]!) {
          insert_simulations(objects: $objects) {
            affected_rows
          }
        }
        """

        # Prepare the payload with variables
        payload = {
            "query": mutation_query,
            "variables": {
                "objects": self.results
            }
        }
        try:
            # Make the HTTP POST request
            response = requests.post(self.hasura_url, headers=self.headers, json=payload)

            # Check the response
            if response.status_code == 200:
                print("Mutation successful")
                print(response.json())
            else:
                print("Mutation failed")
                print(response.text)
        except requests.RequestException as e:
            print(f"Error during HTTP request: {e}")


if __name__ == "__main__": 
    api = HasuraMutaion()
    api.run_mutation()