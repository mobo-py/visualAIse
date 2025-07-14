from gradio_client import Client

client = Client("NihalGazi/FLUX-Pro-Unlimited")
result = client.predict(
		prompt="monkey wearing a space suit, floating in space, digital art",
		width=1280,
		height=1280,
		seed=0,
		randomize=True,
		server_choice="Google US Server",
		api_name="/generate_image"
)
print(result)