import boto3
import botocore.config
import json
from botocore.exceptions import ClientError
from datetime import datetime



def generate_blog_using_bedrock(blog_topic:str)-> str:

    # Create Bedrock client
    client = boto3.client("bedrock-runtime", region_name = "us-west-2")

    # Setting model
    model_id = "meta.llama3-70b-instruct-v1:0"

    #defining prompt
    prompt = f"""Write a blog post about {blog_topic} in 200 words. The blog post should be engaging, informative, and well-structured. It should include an introduction, main body, and conclusion. Use a conversational tone and provide examples to illustrate key points. The blog post should be suitable for a general audience and should not require any prior knowledge of the topic. Please ensure that the content is original and does not contain any plagiarism.

"""
    # Embed prompt in LLama3's instruction format
    formatted_prompt = f"""
<|begin_of_text|><|start_header_id|>user<|end_header_id|>
{prompt}
<|eot_id|>
<|start_header_id|>assistant<|end_header_id|>
"""
    # request payoad
    request_payload = {
        "prompt":formatted_prompt,
        "max_gen_len":512,
        "temperature":0.7,
    }

    # Convert the request payload to JSON string
    request_payload_json = json.dumps(request_payload)

    # Invoke the Bedrock model
    try:
        response = client.invoke_model(modelId = model_id,
                                       body = request_payload_json)
        # Decode response body
        model_response = json.loads(response["body"].read())
        print(model_response)
        # Extracting response text
        generated_blob = model_response["generation"]
        return generated_blob
    except (ClientError, Exception) as e:
        print(f"Error generating the blog:{e}")
        return ""

def save_blog_details_to_s3(s3_bucket:str, s3_key:str, generated_blog:str):
    s3 = boto3.client("s3")
    try:
        s3.put_object(Bucket=s3_bucket, Key=s3_key, Body=generated_blog)
        print(f"Blog saved to S3 bucket: {s3_bucket}, key: {s3_key}")
    except ClientError as e:
        print(f"Error saving blog to S3: {e}")

def lambda_handler(event, context):
    event = json.loads(event["body"])
    blog_topic = event.get("blog_topic")

    generate_blog = generate_blog_using_bedrock(blog_topic)

    if generate_blog:
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        s3_key = f"blog-output/{current_time}.txt"
        s3_bucket = "blog-generation-bedrock-4588"
        save_blog_details_to_s3(s3_bucket, s3_key, generate_blog)
    else:
        print("No blog generated.")

    return {
        "statusCode": 200,
        "body": json.dumps({
            "message": "Blog generation process completed.",
            "blog_topic": blog_topic,
            "s3_bucket": s3_bucket})}


    