import json

from download_models import find_checkpoint_models, load_workflow


def test_load_workflow_and_find_checkpoint_models(tmp_path):
    workflow_path = tmp_path / 'workflow.json'
    workflow_path.write_text(
        json.dumps(
            {
                'nodes': {
                    'checkpoint': {
                        'type': 'CheckpointLoaderSimple',
                        'args': {'checkpoint': 'example/model'},
                    },
                    'other': {'type': 'TextEncode', 'args': {}},
                }
            }
        )
    )

    workflow = load_workflow(workflow_path)

    assert list(find_checkpoint_models(workflow)) == ['example/model']


def test_find_checkpoint_models_ignores_incomplete_nodes():
    workflow = {'nodes': {'empty': {'type': 'CheckpointLoaderSimple', 'args': {}}}}

    assert list(find_checkpoint_models(workflow)) == []
