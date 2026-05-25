import argparse
import json
from pathlib import Path


def load_workflow(path: Path):
    with path.open('r', encoding='utf-8') as f:
        return json.load(f)


def find_checkpoint_models(workflow):
    nodes = workflow.get('nodes', {})
    for node_name, node in nodes.items():
        if node.get('type') == 'CheckpointLoaderSimple':
            checkpoint = node.get('args', {}).get('checkpoint')
            if checkpoint:
                yield checkpoint


def main():
    parser = argparse.ArgumentParser(description='Download ComfyUI model checkpoints used by the VitaDex workflow.')
    parser.add_argument('--workflow', default='card_generation/workflow_api.json', help='Path to ComfyUI workflow JSON file.')
    parser.add_argument('--model-dir', default='models', help='Local base directory for downloaded models.')
    parser.add_argument('--use-safetensors', action='store_true', help='Prefer safetensors if available.')
    parser.add_argument('--revision', default=None, help='Hugging Face model revision to download.')
    args = parser.parse_args()

    try:
        from huggingface_hub import snapshot_download
    except ImportError:
        raise SystemExit('Please install huggingface_hub first: pip install huggingface_hub')

    workflow_path = Path(args.workflow)
    if not workflow_path.exists():
        raise SystemExit(
            f'Workflow file not found: {workflow_path}.\n'
            'Provide a valid `--workflow` path to a ComfyUI workflow JSON file.'
        )

    workflow = load_workflow(workflow_path)
    models = list(dict.fromkeys(find_checkpoint_models(workflow)))
    if not models:
        raise SystemExit('No CheckpointLoaderSimple models found in workflow.')

    model_dir = Path(args.model_dir)
    model_dir.mkdir(parents=True, exist_ok=True)

    print(f'Found {len(models)} model(s) in workflow:')
    for model_id in models:
        print(f' - {model_id}')

    allow_patterns = ['*.json', '*.txt', '*.yaml', '*.pkl']
    if args.use_safetensors:
        allow_patterns.insert(0, '*.safetensors')
    else:
        allow_patterns.insert(0, '*.ckpt')
        allow_patterns.insert(1, '*.safetensors')

    for model_id in models:
        target_dir = model_dir / model_id.replace('/', '_')
        print(f'Downloading model {model_id} into {target_dir}...')
        snapshot_download(
            repo_id=model_id,
            local_dir=target_dir,
            revision=args.revision,
            repo_type='model',
            allow_patterns=allow_patterns,
            ignore_patterns=['*.lock'],
        )
        print(f'  done: {target_dir}')

    print('Download complete. Place the downloaded model directory inside ComfyUI models if necessary.')


if __name__ == '__main__':
    main()
