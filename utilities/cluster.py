from __future__ import print_function


def print_cluster_status(cluster):
    if cluster.scale_settings.auto_scale is None:
        print(
            'Cluster state: {0} Target: {1}; Allocated: {2}; Idle: {3}; '
            'Unusable: {4}; Running: {5}; Preparing: {6}; Leaving: {7}'.format(
                cluster.allocation_state,
                cluster.scale_settings.manual.target_node_count,
                cluster.current_node_count,
                cluster.node_state_counts.idle_node_count,
                cluster.node_state_counts.unusable_node_count,
                cluster.node_state_counts.running_node_count,
                cluster.node_state_counts.preparing_node_count,
                cluster.node_state_counts.leaving_node_count))
    else:
        print(
            'Cluster state: {0} Min: {1}; Max: {2}; Initial: {3}; Allocated: {4}; Idle: {5}; '
            'Unusable: {6}; Running: {7}; Preparing: {8}; Leaving: {9}'.format(
                cluster.allocation_state,
                cluster.scale_settings.auto_scale.minimum_node_count,
                cluster.scale_settings.auto_scale.maximum_node_count,
                cluster.scale_settings.auto_scale.initial_node_count,
                cluster.current_node_count,
                cluster.node_state_counts.idle_node_count,
                cluster.node_state_counts.unusable_node_count,
                cluster.node_state_counts.running_node_count,
                cluster.node_state_counts.preparing_node_count,
                cluster.node_state_counts.leaving_node_count))
 
    if not cluster.errors:
        return
    for error in cluster.errors:
        print('Cluster error: {0}: {1}'.format(error.code, error.message))
        if error.details:
            print('Details:')
            for detail in error.details:
                print('{0}: {1}'.format(detail.name, detail.value))
