from flask import Flask, request, jsonify
from flask_cors import CORS
from embedding import Embedding
import numpy as np
from sklearn.decomposition import PCA
from sklearn.manifold import TSNE
from sklearn.cluster import DBSCAN
import json
import pickle
import os
import base64
import subprocess
import sys

# Get the directory of the current script
current_dir = os.path.dirname(os.path.abspath(__file__))

# Change to the backend directory
os.chdir(current_dir)
sys.path.insert(0, current_dir)

# Print current working directory for verification
print(f"Working directory changed to: {os.getcwd()}")

app = Flask(__name__)
CORS(app)
OLLAMA_API_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL_NAME = "gemma3:4b"
path_prefixes = {'p':'../frontend/public/external_images/p_crop_trans/', 
                 'OH':'../frontend/public/external_images/imgs/oh_trans/', 
                 'Mach':'../frontend/public/external_images/imgs/mach_trans/'}

# create a list of Embedding objects
# embnpy = np.load('blip2_mean_pooling.npy')
# fnamenpy = np.load('blip2_filenames.npy')
embnpy = np.load('npys/InternViT-6B-448px-V2_5_mean_2.npy')
fnamenpy = np.load('npys/InternViT-6B-448px-V2_5_filenames_all.npy')
# embnpy_p = np.load('InternViT-6B-448px-V2_5_mean_2.npy')
# fnamenpy_p = np.load('InternViT-6B-448px-V2_5_filenames_all.npy')

emb_list = [Embedding(emb, fname) for emb, fname in zip(embnpy, fnamenpy)]
# emb_list_p = [Embedding(emb, fname) for emb, fname in zip(embnpy_p, fnamenpy_p)]

# create lists of Embedding objects for each variable
var_list_dict = {}
vars = ['p', 'OH', 'Mach']
for var in vars:
    var_list_dict[var] = [obj for obj in emb_list if obj.variable == var]
    var_list_dict[var].sort(key=lambda x: (x.case, x.time))
# var_list_dict['p'] = [obj for obj in emb_list_p if obj.variable == 'p']
# var_list_dict['p'].sort(key=lambda x: (x.case, x.time))

# read description from a json file
fname_desc_dict = {} # dict to store desc objects index
descFile = 'descFile.json'
case_desc_dict = {}
case_desc_file = 'case_desc.json'

if not os.path.exists(descFile):
    # Create an empty JSON file if it doesn't exist
    with open(descFile, 'w') as f:
        json.dump({}, f)
else:
    with open(descFile, 'r') as f:
        fname_desc_dict = json.load(f)

if not os.path.exists(case_desc_file):
    # Create an empty JSON file if it doesn't exist
    with open(case_desc_file, 'w') as f:
        json.dump({}, f)
else:
    with open(case_desc_file, 'r') as f:
        case_desc_dict = json.load(f)

fname_emb_dict = {}
for idx, emb in enumerate(emb_list):
    fname_emb_dict[emb.fname] = emb        
for fname, desc in fname_desc_dict.items():
    if fname in fname_emb_dict:
        emb = fname_emb_dict[fname]
        emb.description = desc    
    
selected_vars = []    
    
@app.route('/cases', methods=['POST'])
def handle_post_request():
    # Retrieve data from the request body
    data = request.json  # Expecting JSON data
    
    # Access specific fields from the data
    p_range = data.get('pRange')
    t_range = data.get('tRange')
    h2o_range = data.get('h2oRange')

    # Process the data
    filtered_cases = []
    for emb in emb_list:
        case_dict = {"case": emb.case, "t": round(emb.t, 2), "h2o": round(emb.h2o * 100, 2), "p": round(emb.p, 3)}
        if emb.p >= p_range[0] and emb.p <= p_range[1] and emb.t >= t_range[0] and emb.t <= t_range[1] and emb.h2o * 100 >= h2o_range[0] and emb.h2o * 100 <= h2o_range[1] and case_dict not in filtered_cases:
            filtered_cases.append(case_dict)
    # print(filtered_cases)

    return jsonify(filtered_cases)

# Cache for storing previous coordinate results
coordinates_cache = {
    'request_hash': None,
    'result': None
}


@app.route('/coordinates', methods=['POST'])
def get_coordinates():
    data = request.json  # Expecting JSON data
    selectedCases_dict = data.get('selectedCases')
    selectedComponent = data.get('selectedComponent')
    eps = data.get('eps')
    min_samples = data.get('minSamples')
    selectedCases = [case['case'] for case in selectedCases_dict]
    var_list = [obj for obj in var_list_dict[selectedComponent] if obj.case in selectedCases]
    global selected_vars
    selected_vars = var_list
    
    # PCA to reduce dimensionality
    var_embs = np.array([p.emb for p in var_list])
    pca = PCA(n_components=128, random_state=42)
    pca.fit(var_embs)
    pca_embs = pca.transform(var_embs)
    
    # Use t-SNE to visualize the embeddings
    tsne = TSNE(n_components=2, n_jobs=-1, random_state=42)
    tsne_xys = tsne.fit_transform(pca_embs)
    
    # use umap instead of t-SNE for faster computation
    # from umap import UMAP
    # tsne = UMAP(n_components=2, n_neighbors=15, min_dist=0.1, metric='euclidean', random_state=42)
    # tsne_xys = tsne.fit_transform(pca_embs)
    
    # trustworthiness evaluation
    # from sklearn.manifold import trustworthiness
    # trust = trustworthiness(pca_embs, tsne_xys, n_neighbors=10)
    # print(f"Trustworthiness: {trust}")
    
    # Use DBSCAN to cluster the embeddings
    dbscan = DBSCAN(eps=eps, min_samples=min_samples).fit(pca_embs)
    labels = dbscan.labels_
    unique_labels = set(labels)
    
    # Calculate silhouette score
    # from sklearn.metrics import silhouette_score
    # if len(unique_labels) > 1:
    #     mask = labels != -1  # Exclude noise points
    #     silhouette_avg = silhouette_score(pca_embs[mask], labels[mask])
    #     print(f"Silhouette Score: {silhouette_avg}")
    # else:
    #     silhouette_avg = -1
    #     print("Silhouette Score: Not applicable (only one cluster)")
    
    # Calculate the centroid of each cluster
    distinct_labels = np.unique(labels)
    centroids = []
    centroid_indices = []
    is_centroid = [False] * len(var_list)
    for label in distinct_labels:
        xys = tsne_xys[labels == label]
        centroid = np.mean(xys, axis=0)
        
        # find the closest point to the centroid
        closest_idx = np.argmin(np.linalg.norm(xys - centroid, axis=1))
        
        # find the corresponding Embedding object
        indices = np.where(labels == label)[0]
        emb = var_list[indices[closest_idx]]
        centroid_indices.append(int(indices[closest_idx]))
        centroids.append(emb)
        emb.iscentroid = True
        is_centroid[indices[closest_idx]] = True
    
    case_xys_dict = {}
    for idx, var in enumerate(var_list):
        if var.case not in case_xys_dict:
            case_xys_dict[var.case] = []
        case_xys_dict[var.case].append(tsne_xys[idx].tolist())
    
    result = {
        'pca_embs': pca_embs.tolist(),
        'tsne_xys': tsne_xys.tolist(),
        'labels': labels.tolist(),
        'cluster_count': len(unique_labels),
        'fnames': [emb.fname for emb in var_list],
        'times': [int(emb.time) for emb in var_list],
        'cases': [emb.case for emb in var_list],
        'case_xys_dict': case_xys_dict,
        'iscentroid': is_centroid,
        'centroid_indices': centroid_indices,
        'descriptions': [emb.description for emb in var_list],
        'case_desc_dict': case_desc_dict,
    }
    
    return jsonify(result)


@app.route('/coordinates_test', methods=['POST'])
def get_coordinates_test():
    global descriptions
    data = request.json
    selectedCases_dict = data.get('selectedCases')
    
    # pklfname = 'blip2test_p_var_list.pkl'
    pklfname = 'internvit2_var_list.pkl'
    
    with open(pklfname, 'rb') as f:
        p_list_fixed = pickle.load(f)
    
    selectedCases = [case['case'] for case in selectedCases_dict]
    p_list_selected = [p for p in p_list_fixed if p.case in selectedCases]
    
    case_xys_dict = {}
    tsne_xys = [p.xy.tolist() for p in p_list_selected]
    labels = [int(p.label) for p in p_list_selected]
    unique_labels = set(labels)
    iscentroid = [p.iscentroid for p in p_list_selected]
    if descriptions == []:
        descriptions = [p.description for p in p_list_selected]
    
    for idx, var in enumerate(p_list_selected):
        if var.case not in case_xys_dict:
            case_xys_dict[var.case] = []
        case_xys_dict[var.case].append(tsne_xys[idx])
    
    result = {
        'tsne_xys': tsne_xys,
        'labels': labels,
        'cluster_count': len(unique_labels),
        'fnames': [emb.fname for emb in p_list_selected],
        'times': [emb.time for emb in p_list_selected],
        'cases': [emb.case for emb in p_list_selected],
        'iscentroid': iscentroid,
        'centroid_indices': [idx for idx, emb in enumerate(p_list_selected) if emb.description],
        'descriptions': [emb.description for emb in p_list_selected],
        'case_xys_dict': case_xys_dict,
    }
    res = jsonify(result)
    return res

    
@app.route('/update_description', methods=['POST'])
def update_description():
    data = request.json
    # index = data.get('index')
    description = data.get('description')
    # comp = data.get('component')
    fileName = data.get('fileName')
    emb = fname_emb_dict[fileName]
    emb.description = description
    if description == '' and fileName in fname_desc_dict:
        del fname_desc_dict[fileName]
    else:
        fname_desc_dict[fileName] = description
    # Save the updated descriptions to the JSON file
    with open(descFile, 'w') as f:
        json.dump(fname_desc_dict, f)
    
    return jsonify({'success': True})


@app.route('/update_case_description', methods=['POST'])
def update_case_description():
    data = request.json
    caseName = data.get('caseName')
    description = data.get('description')
    component = data.get('component')
    
    if caseName in case_desc_dict:
        case_desc_dict[caseName][component] = description
    else:
        case_desc_dict[caseName] = {component: description}
    
    # Save the updated case descriptions to the JSON file
    with open(case_desc_file, 'w') as f:
        json.dump(case_desc_dict, f)
    
    return jsonify({'success': True})


def image_to_base64(image_path):
    """
    Convert an image to base64 encoding
    """
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def generate_description_with_ollama(model_name, image_paths, prompts, **options):
    """
    Generate a description using the local ollama model with multiple images and prompts
    """
    import requests
    
    # Convert all images to base64
    images_base64 = [image_to_base64(img_path) for img_path in image_paths]
    
    # Ensure prompts and images can be interleaved
    max_length = max(len(prompts), len(images_base64))
    
    # Build an interleaved prompt
    combined_prompt = ""
    for i in range(max_length):
        # Add prompt if available
        if i < len(prompts):
            combined_prompt += prompts[i] + "\n"
        
        # Mark where each image should be positioned in the text
        if i < len(images_base64):
            combined_prompt += f"[IMAGE_{i}]\n"
    
    data = {
        "model": model_name,
        "options": options,
        "prompt": combined_prompt,
        "images": images_base64,
        "stream": False
    }
    
    try:
        response = requests.post(OLLAMA_API_URL, json=data)
        response.raise_for_status()
        return response.json().get('response', 'No response received')
    except requests.exceptions.RequestException as e:
        return f"Error making request: {e}"
    except ValueError:
        return "Error: Failed to decode JSON response"
    
    
# Define the prompt for image description
prompt_p = """
You are an expert on scramjet combustor and fluid dynamics.
This is an image of pressure field inside a scramjet combustor.
Blue represents low pressure and red represents high pressure.
The fuel injector is located at the top of the combustor and has the highest pressure.
The air comes from the entrance located at the left edge of the image, 
while the exit of the combustor is located at the right side.
Please describe the image in detail, focusing on the pressure distribution, flow features, 
and potential implications for combustion efficiency based on the given images and descriptions below.
"""


@app.route('/generate_description', methods=['POST'])
def generate_description():
    data = request.json
    index = data.get('index')
    comp = data.get('component')
    path_prefix = path_prefixes[comp]
    img_path = path_prefix + selected_vars[index].fname
    
    # find at most 5 closest centroids with descriptions
    centroids = [emb for emb in selected_vars if emb.iscentroid and emb.description is not None]
    if len(centroids) > 0:
        centroid_embs = np.array([c.emb for c in centroids])
        target_emb = selected_vars[index].emb
        distances = np.linalg.norm(centroid_embs - target_emb, axis=1)
        closest_indices = np.argsort(distances)[:min(5, len(centroids))]
        img_paths = [img_path] + [path_prefix + centroids[i].fname for i in closest_indices]
        prompts = [prompt_p] + [centroids[i].description for i in closest_indices]
    else:
        img_paths = [img_path]
        prompts = [prompt_p]
        
    description = generate_description_with_ollama(OLLAMA_MODEL_NAME, img_paths, prompts, num_ctx=8192)
    
    return jsonify({'success': True, 'description': description})

@app.route('/case_description', methods=['POST'])
def generate_case_description():
    data = request.json
    caseName = data.get('caseName')
    component = data.get('component')
    caseIndices = data.get('caseIndices')
    
    prompt_case_p = """
    You are an expert on scramjet combustor and fluid dynamics.
    The images are temporal flow fields inside a scramjet combustor of a simulation case. And some images have their descriptions.
    Please summarize the case by describing the flow features and combustion evolution based on the given images and descriptions.
    """
    prompts = []
    case_img_paths = [path_prefixes[component] + selected_vars[i].fname for i in caseIndices]
    for i in caseIndices:
        if selected_vars[i].description is not None:
            prompts.append(selected_vars[i].description)
        else:
            prompts.append('')
    prompts.append(prompt_case_p)
    description = generate_description_with_ollama(OLLAMA_MODEL_NAME, case_img_paths, prompts, num_ctx=16384)
    return jsonify({'success': True, 'description': description})

if __name__ == '__main__':
    app.run(debug=True)
