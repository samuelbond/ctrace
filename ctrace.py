
import docker
import datetime
import argparse
from graph_tool.all import *
from texttable import Texttable

client = docker.APIClient()
table = Texttable()
table.add_row(['Container Name', 'Network Ids', 'IPv4 Addresses'])
summary = {}


def get_candidate_containers(tc_name, existing_network_ids=None):
    if existing_network_ids is None:
        existing_network_ids = []
    target_container_info = client.inspect_container(tc_name)
    candidate_containers = {}
    candidate_networks = []
    for network_id in target_container_info['NetworkSettings']['Networks']:
        if network_id not in existing_network_ids:
            candidate_networks.append(network_id)
            network_containers = client.inspect_network(network_id)['Containers']
            candidate_containers.__setitem__(network_id, {})
            for container_id, container_value in network_containers.items():
                container_name = container_value['Name']
                container_ip_addr = container_value['IPv4Address'].split('/', 1)[0]

                if container_name not in summary:
                    summary.__setitem__(container_name, [container_name,
                                                         network_id,
                                                         container_ip_addr])
                else:
                    sum_value = summary[container_name]
                    if network_id != sum_value[1]:
                        summary.__setitem__(container_name, [container_name,
                                                             sum_value[1]+', '+network_id,
                                                             sum_value[2]+', '+container_ip_addr])

                if container_name != tc_name:
                    candidate_containers[network_id].__setitem__(container_name,
                                                                 {'Name': container_name,
                                                                  'IPv4Address': container_ip_addr})
    if candidate_networks.__len__() > 0:
        return candidate_containers, candidate_networks
    return None, None


def pop_all_out_into_list(input_dict):
    output_list = []
    for dict_key, dict_value in input_dict.items():
        output_list.append(input_dict[dict_key])

    return output_list


if __name__ == '__main__':
    start_time = datetime.datetime.now()
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument('container', help='The target container', type=str)
    args = arg_parser.parse_args()
    target_container_name = args.container
    print('Finding candidate artifacts for target artifact: {} ...'.format(target_container_name))
    first_gen_candidate_containers, existing_candidate_networks = \
        get_candidate_containers(target_container_name)
    if first_gen_candidate_containers is not None:
        candidate_containers_tree = {target_container_name:
                                         pop_all_out_into_list(first_gen_candidate_containers)}

        for f_key, f_value in first_gen_candidate_containers.items():
            for f_container_name in f_value:
                sec_candidate_containers, sec_candidate_networks = \
                    get_candidate_containers(f_container_name, existing_candidate_networks)
                if sec_candidate_containers is not None:
                    existing_candidate_networks.extend(sec_candidate_networks)
                    candidate_containers_tree.__setitem__(f_container_name,
                                                          pop_all_out_into_list(
                                                              sec_candidate_containers)
                                                          )

        undirected_graph = Graph(directed=False)
        vertex_prop = undirected_graph.new_vertex_property("string")

        vertices = {}
        for root, children in candidate_containers_tree.items():
            if root not in vertices.keys():
                vertices[root] = undirected_graph.add_vertex()
                vertex_prop[vertices[root]] = root
            for item in children:
                for child in item:
                    vertices[child] = undirected_graph.add_vertex()
                    vertex_prop[vertices[child]] = child
                    undirected_graph.add_edge(vertices[root], vertices[child])

        for root, children in candidate_containers_tree.items():
            for item in children:
                all_items = pop_all_out_into_list(item)
                item_size = len(all_items)
                relations = []
                for child in item:
                    k = 1
                    for i in range(item_size):
                        item_index = k
                        if item_index < item_size:
                            item_key = all_items[item_index]['Name']
                            relation_name = child + ':' + item_key
                            relation_name_inverse = item_key + ':' + child
                            if child != item_key:
                                if relation_name not in relations \
                                        and relation_name_inverse not in relations:
                                    undirected_graph.add_edge(vertices[child], vertices[item_key])
                                    relations.append(relation_name)
                        k += 1
        print('Drawing relation graph ...')
        graph_draw(undirected_graph, vertex_text=vertex_prop, vertex_font_size=18,
                   bg_color=[1, 1, 1, 1], output="two-nodes.png")
        print('Completed with the following summary:')
        for summary_key, summary_row in summary.items():
            table.add_row(summary_row)

        print(table.draw())
        duration = datetime.datetime.now() - start_time
        print("Elapsed Time: {}sec {}ms {}microseconds".
              format(duration.seconds, int(duration.seconds)/1000, duration.microseconds))


