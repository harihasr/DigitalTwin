# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from rest_framework.views import APIView
from rest_framework.authentication import BasicAuthentication, TokenAuthentication
from rest_framework_jwt.authentication import JSONWebTokenAuthentication
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from django.http import HttpResponse, JsonResponse
from .models import Project, Connector, Machine, Simulation
from .serializers import ProjectSerializer, ConnectorSerializer, MachineSerializer, SimulationSerializer
from http import HTTPStatus
import json
import os
import socket
import requests
import sys

CUR_DIR = os.path.abspath(os.path.dirname(__file__))
PROJECTS_FOLDER = os.path.join(os.path.dirname(CUR_DIR), 'Projects')
if not os.path.isdir(PROJECTS_FOLDER):
    os.makedirs(PROJECTS_FOLDER)

config_file = os.path.join(CUR_DIR, 'server.config')
if not os.path.isfile(config_file):
    print('Sever config file not found at "{}"'.format(config_file))
    sys.exit(-1)

with open(config_file, 'r') as f:
    try:
        config_dict = json.load(f)
        REST_API_PORT = config_dict['rest_api_port']
        PROJECTS_SERVER_PORT = config_dict['projects_server_port']
    except Exception as e:
        print('Invalid config file')
        print('{}'.format(e))


# List of projects \projects GET AND POST
class ProjectList(APIView):
    permission_classes = (IsAuthenticatedOrReadOnly, )
    authentication_classes = (BasicAuthentication, JSONWebTokenAuthentication)

    def get(self, request):

        """
        This API gets the list of projects from the database.

        Expected Headers: None

        Expected Payload: None

        Response Message:

            {
                "projects": []
            }

        """
        projects = Project.objects.all()
        serializer = ProjectSerializer(projects, many=True)
        return JsonResponse({'projects': [data['name'] for data in serializer.data]})

    def post(self, request):

        """
        This API POSTs a project to the server if it doesn't already exist.

        Expceted Headers:{

            'Content-Type': 'text/json'

        }

        Expected Payload:{

            'name': 'project_name'

        }

        Response Message:

            Response Code:
                "201":
                    description: Status OK. Project Created.
                "409":
                    description: Conflict. Project already exists.
                default:
                    description: Unexpected Error.
        """
        body = request.body.decode("utf-8")
        print(body)
        print(request.META)
        if not body:
            return HttpResponse(status=HTTPStatus.BAD_REQUEST)

        data = json.loads(body)
        project_name = data['name']
        projects = Project.objects.all()
        serializer = ProjectSerializer(projects, many=True)
        existing_projects = [project['name'] for project in serializer.data]
        if project_name in existing_projects:
            return Response(status=HTTPStatus.CONFLICT)

        project_location = os.path.join(PROJECTS_FOLDER, project_name+'.aedt')
        project = Project.objects.create(name=project_name, project_location=project_location)
        project.save()
        return HttpResponse(HTTPStatus.OK)


# \projects\name GET AND POST
class ProjectDetails(APIView):
    permission_classes = (IsAuthenticatedOrReadOnly,)
    authentication_classes = (BasicAuthentication, JSONWebTokenAuthentication)
    def get(self, request, p_name):

        """
        Given the project name, get the details related to the project.
        ---
        Parameters:[

            {
                "name": p_name,
                "description": Project Name,
                "required": true,
                "type": string,
                "paramType": path
            }

        ]

        Expected Headers: None

        Expected Payload: None

        Response Message:

            {
                "name": "project_name",
                "project_location": "Location of the project on the server"
            }

        """

        projects = Project.objects.get(name=str(p_name))
        serializer = ProjectSerializer(projects, many=False)
        return JsonResponse({'name': serializer.data['name'], 'project_location': serializer.data['project_location']})

    def delete(self, request, p_name):
        """
        Delete project, if it exists.

        Parameters:[

            {
                "name": p_name,
                "description": Project Name,
                "required": true,
                "type": string,
                "paramType": path
            }

        ]

        Expected Headers: None

        Expected Payload: None

        Response Message:

            Response Code:
                "200":
                    description: Status OK. Project Deleted.
                default:
                    description: Unexpected Error.
        """
        project = Project.objects.get(name=p_name)
        connectors = project.connector_set.all()
        connectors.delete()
        if os.path.isfile(project.project_location):
            os.remove(project.project_location)
        project.delete()
        return HttpResponse(HTTPStatus.OK)


# \projects\name\status, \projects\name\project_location ONLY GET
# class ProjectStatus(APIView):
#     def get(self, request, p_name, attribute):
#         projects = Project.objects.get(name=str(p_name))
#         serializer = ProjectSerializer(projects, many=False)
#         return JsonResponse({attribute: serializer.data[attribute]})


# \projects\name\connectors
class Connectors(APIView):
    permission_classes = (IsAuthenticatedOrReadOnly,)
    authentication_classes = (BasicAuthentication, JSONWebTokenAuthentication)
    def get(self, request, p_name):
        """
        Get list of connectors for a given project.

        Parameters:[

            {
                "name": p_name,
                "description": Project Name,
                "required": true,
                "type": string,
                "paramType": path
            }

        ]

        Expected Headers: None

        Request Payload: None

        Response Message:

            {
                "connectors": []
            }

            Response Code:
                "200":
                        description: Status OK. Request Successful.
                default:
                        description: Unexpected Error.
        """

        project = Project.objects.get(name=p_name)
        connectors = project.connector_set.all()
        serializer = ConnectorSerializer(connectors, many=True)
        return JsonResponse({'connectors': [data['name'] for data in serializer.data]})

    def post(self, request, p_name):
        """
        POST a connector to a project.

        Parameters:[

            {
                "name": p_name,
                "description": Project Name,
                "required": true,
                "type": string,
                "paramType": path
            }

        ]

        Expected Headers:{

            "Content-Type": 'text/json'

        }

        Expected Payload:{

            "name": "",
            "from_simulation": "",
            "to_simulation": "",
            "Port": "",
            "ConnectionTimeout": "",
            "IOTimeout": "",
            "TS": "",
            "SyncToRT": ""

        }

        Response Message:

            Response Code:
                "201":
                    description: Status OK. Connector Created.
                "409":
                    description: Conflict. Connector already exists.
                default:
                    description: Unexpected Error.
        """
        body = request.body.decode("utf-8")
        if not body:
            return HttpResponse(status=HTTPStatus.BAD_REQUEST)
        data = json.loads(body)
        project = Project.objects.get(name=p_name)
        connectors = project.connector_set.all()
        serializer = ConnectorSerializer(connectors, many=True)
        existing_connectors = [d['name'] for d in serializer.data]
        if data['name'] in existing_connectors:
            return HttpResponse(status=HTTPStatus.CONFLICT)

        if project:
            connector = Connector.objects.create(name=data['name'], ts=data['TS'], sync_to_rt=data['SyncToRT'],
                                                 ip_address='', host_name='',
                                                 port=data['Port'], conn_timeout=data['ConnectionTimeout'],
                                                 io_timeout=data['IOTimeout'], from_simulation=data['from_simulation'],
                                                 to_simulation=data['to_simulation'], project=project)
            connector.save()
            print("Before Return 200")
            return HttpResponse(HTTPStatus.OK)
        return HttpResponse(status=404)


# \projects\name\connectors\conn_name GET
class ConnectorList(APIView):
    permission_classes = (IsAuthenticatedOrReadOnly,)
    authentication_classes = (BasicAuthentication, JSONWebTokenAuthentication)

    def get(self, request, p_name, conn_name):
        """
        Query connector by connector name and get all its attributes

        Parameters:[

            {
                "name": p_name,
                "description": Project Name,
                "required": true,
                "type": string,
                "paramType": path
            }

            {
                "name": conn_name,
                "description": Connector Name,
                "required": true,
                "type": string,
                "paramType": path

            }

        ]

        Expected Headers: None

        Request Payload: None

        Response Message:

            {
                "name": "",
                "from_simulation": "",
                "to_simulation": "",
                "Port": "",
                "ConnectionTimeout": "",
                "IOTimeout": "",
                "TS": "",
                "SyncToRT": "",
            }

            Response Code:
                "200":
                    description: Status OK. Request Successful.
                default:
                    description: Unexpected Error.
        """
        project = Project.objects.get(name=p_name)
        connector = project.connector_set.filter(name=conn_name)
        serializer = ConnectorSerializer(connector[0], many=False)
        # Not modifying this as it works in tandem with the Thingworx app.
        return Response(serializer.data)

    # def post(self, request, p_name):
    #     data = json.loads(request.body)
    #     project = Project.objects.get(name=p_name)
    #     if(project):
    #         connector = Connector.objects.create(name=data['name'], ts=data['ts'], sync_to_rt=data['sync_to_rt'],
    #                                              ip_address=data['ip_address'], host_name=data['host_name'],
    #                                              port=data['port'], conn_timeout=data['conn_timeout'],
    #                                              io_timeout=data['io_timeout'],
    #                                              from_simulation=data['from_simulation'],
    #                                              to_simulation=data['to_simulation'], project=project)
    #         connector.save()
    #         return HttpResponse()
    #     return HttpResponse(status=404)


# \projects\name\connector\name\attribute\ ONLY GET
class ConnectorDetails(APIView):
    permission_classes = (IsAuthenticatedOrReadOnly,)
    authentication_classes = (BasicAuthentication, JSONWebTokenAuthentication)

    def get(self, request, p_name, conn_name, attribute):
        """
        Query Connector by attribute and get it's value

        Parameters:[

            {
                "name": p_name,
                "description": Project Name,
                "required": true,
                "type": string,
                "paramType": path
            }

            {
                "name": conn_name,
                "description": Connector Name,
                "required": true,
                "type": string,
                "paramType": path

            }

            {
                "name": attribute,
                "description": Connector Attribute,
                "required": true,
                "type": string,
                "paramType": path
            }

        ]

        Expected Headers: None

        Request Payload: None

        Response Message:

            {
                "connector_attribute": "value"
            }

            Response Code:
            "200":
                    description: Status OK. Request Successful.
            default:
                    description: Unexpected Error.
        """
        project = Project.objects.get(name=p_name)
        connector = project.connector_set.filter(name=conn_name)
        serializer = ConnectorSerializer(connector[0], many=False)
        return JsonResponse({attribute: serializer.data[attribute]})


# \projects\name\connector\name\ ONLY POST/UPDATE
class ConnectorEdit(APIView):
    permission_classes = (IsAuthenticatedOrReadOnly,)
    authentication_classes = (BasicAuthentication, JSONWebTokenAuthentication)

    def post(self, request, p_name, conn_name):
        """
        POST or Update one or more attributes of the connector.

        Parameters:[

            {
                "name": p_name,
                "description": Project Name,
                "required": true,
                "type": string,
                "paramType": path
            }

            {
                "name": conn_name,
                "description": Connector Name,
                "required": true,
                "type": string,
                "paramType": path

            }

        ]

        Expected Headers:{

            "Content-Type": 'text/json'

        }

        Expected Payload:{

            'connector_attribute': value

        }

        Response Message:

            Response Code:
            "200":
                    description: Status OK. Request Successful.
            default:
                    description: Unexpected Error.

        """
        data = json.loads(request.body)
        connector = Connector.objects.get(name=conn_name)
        if data['ts']:
            connector.ts = data['ts']
        if data['sync_to_rt']:
            connector.sync_to_rt = data['sync_to_rt']
        if data['ip_address']:
            connector.ip_address = data['ip_address']
        if data['host_name']:
            connector.host_name = data['host_name']
        if data['port']:
            connector.port = data['port']
        if data['conn_timeout']:
            connector.conn_timeout = data['conn_timeout']
        if data['io_timeout']:
            connector.io_timeout = data['io_timeout']
        if data['from_simulation']:
            connector.from_simulation = data['from_simulation']
        if data['to_simulation']:
            connector.to_simulation = data['to_simulation']
        connector.save()
        return HttpResponse(HTTPStatus.OK)


# \machines
class Machines(APIView):
    permission_classes = (IsAuthenticatedOrReadOnly,)
    authentication_classes = (BasicAuthentication, JSONWebTokenAuthentication, TokenAuthentication)

    def get(self, request):
        """
        GET list of machines on the server

        Expected Headers: None

        Request Payload: None

        Response Message:

            {
                "machines": []
            }

            Response Code:
            "200":
                    description: Status OK. Request Successful.
            default:
                    description: Unexpected Error.
        """
        machines = Machine.objects.all()
        serializer = MachineSerializer(machines, many=True)
        return JsonResponse({'machines': [data['name'] for data in serializer.data]})

    def post(self, request):
        """
        POST machines to the server if it doesn't already exist

        Expected Headers:{

            "Content-Type": 'text/json'

        }

        Expected Payload:{

            'name': '',
            'address': '',
            'agent_port': ''

        }

        Response Message:

            Response Code:
            "201":
                    description: Status OK. Machine created.
            "409":
                    description: Conflict. Machine already exists.
            default:
                    description: Unexpected Error.
        """
        body = request.body.decode("utf-8")
        if not body:
            return HttpResponse(status=HTTPStatus.BAD_REQUEST)

        data = json.loads(body)

        machine_name = data['name']
        machines = Machine.objects.all()

        # Case where a machine's address has to be updated.
        # try:
        #     machine = Machine.objects.filter(name=machine_name)
        #     machine.address = data['address']
        #     machine.agent_port = data['agent_port']
        #     machine.save()
        # except Exception as e:
        #     # continue the usual POST request
        #     pass

        serializer = MachineSerializer(machines, many=True)
        existing_machines = [project['name'] for project in serializer.data]

        if machine_name in existing_machines:

            return Response(status=HTTPStatus.CONFLICT)

        machine = Machine.objects.create(name=machine_name, address=data['address'], agent_port=data['agent_port'])
        machine.save()
        return HttpResponse(HTTPStatus.OK)


# \machines\m_name
class MachineDetails(APIView):
    permission_classes = (IsAuthenticated,)
    authentication_classes = (BasicAuthentication, JSONWebTokenAuthentication, TokenAuthentication)

    def get(self, request, m_name):
        """
        Query by machine name, get the address and the agent port of the machine

        Parameters:[

            {
                "name": m_name,
                "description": Machine Name,
                "required": true,
                "type": string,
                "paramType": path
            }

        ]

        Expected Headers: None

        Request Payload: None

        Response Message:

            {
                "name": '',
                "address": '',
                "agent_port": ''
            }

            Response Code:
            "200":
                    description: Status OK. Request Successful.
            default:
                    description: Unexpected Error.
        """
        machines = Machine.objects.get(name=str(m_name))
        serializer = MachineSerializer(machines, many=False)
        return Response(serializer.data)

    def delete(self, request, m_name):
        """
        Delete a machine from the server by name

        Parameters:[

            {
                "name": m_name,
                "description": Machine Name,
                "required": true,
                "type": string,
                "paramType": path
            }

        ]

        Expected Headers: None

        Request Payload: None

        Response Message:

            Response Code:
            "200":
                    description: Status OK. Request Successful.
            default:
                    description: Unexpected Error.
        """
        machine = Machine.objects.get(name=m_name)
        machine.delete()
        return HttpResponse(HTTPStatus.OK)


# \simulations GET
class Simulate(APIView):
    permission_classes = (IsAuthenticated,)
    authentication_classes = (JSONWebTokenAuthentication, BasicAuthentication, TokenAuthentication)

    def get(self, request):
        """
        Get the list of simulations currently running on the client

        Expected Headers: None

        Request Payload: None

        Response Message:

            {
                "simulations": []
            }

            Response Code:
            "200":
                    description: Status OK. Request Successful.
            default:
                    description: Unexpected Error.
        """
        simulations = Simulation.objects.all()
        serializer = SimulationSerializer(simulations, many=True)
        return JsonResponse({'simulations': [data['id'] for data in serializer.data]})

    def post(self, request):
        """
        POST a currently running Simulation to the server

        Expected Headers:{

            "Content-Type": 'text/json'

        }

        Expected Payload:{

            'project': 'project_name',
            'machine': 'machine_name'

        }

        Response Message:

            Response Code:
            "201":
                    description: Status OK. Simulation entry created.
            "409":
                    description: Conflict. Simulation already exists.
            default:
                    description: Unexpected Error.
        """
        body = request.body.decode("utf-8")
        if not body:
            return HttpResponse(status=HTTPStatus.BAD_REQUEST)

        data = json.loads(body)

        project_name = data['project']
        machine_name = data['machine']
        machine = Machine.objects.get(name=machine_name)
        project = Project.objects.get(name=project_name)

        simulation = Simulation.objects.create(project=project.name, machine=machine.name)

        hostname = socket.gethostname()
        (_, _, ipaddrlist) = socket.gethostbyname_ex(hostname)
        ip = ipaddrlist[0]
        print('IP: ', ip)

        file_location = 'http://{}:{}/{}'.format(ip, PROJECTS_SERVER_PORT, project_name+'.aedt')
        connectors = project.connector_set.all()
        serializer = ConnectorSerializer(connectors, many=True)
        try:
            connector_port = serializer.data[0]['port']
        except Exception as e:
            print("No Connectors available: ", str(e))
            return HttpResponse(status=HTTPStatus.BAD_REQUEST)

        address = '{}:{}'.format(ip, REST_API_PORT)
        payload = {'project_location': file_location, 'connector_port': connector_port, 'server_address': address, 'simulation_id': str(simulation.id)}
        url = 'http://{}:{}/deploy/'.format(machine.address, machine.agent_port)
        response = requests.post(url, data=json.dumps(payload))
        if response == HTTPStatus.CREATED:
            simulation.save()
            HttpResponse(HTTPStatus.CREATED)
        else:
            HttpResponse(HTTPStatus.INTERNAL_SERVER_ERROR)


# \simulations\id
class SimulationDetail(APIView):
    permission_classes = (IsAuthenticated,)
    authentication_classes = (JSONWebTokenAuthentication, BasicAuthentication, TokenAuthentication)

    def delete(self, request, s_id):
        """
        Delete simulation from the list of currently on going simulations if this simulation is completed

        Parameters:[

            {
                "name": s_id,
                "description": Simulation ID,
                "required": true,
                "type": string,
                "paramType": path
            }

        ]

        Expected Headers: None

        Request Payload: None

        Response Message:

            Response Code:
            "200":
                    description: Status OK. Request Successful.
            default:
                    description: Unexpected Error.
        """
        simulation = Simulation.objects.get(id=s_id)
        simulation.delete()
        return HttpResponse(HTTPStatus.OK)


# \upload_project\p_name
class UploadProject(APIView):
    permission_classes = (IsAuthenticatedOrReadOnly,)
    authentication_classes = (JSONWebTokenAuthentication, TokenAuthentication)

    def post(self, request, p_name):
        """
        Upload a project file on to the server

        Parameters:[

            {
                "name": p_name,
                "description": Project Name,
                "required": true,
                "type": string,
                "paramType": path
            }

        ]

        Expected Headers:{

            'Content-type': 'multipart/form-data'

        }

        Request Payload:{

            'data': file_data

        }

        Response Message:

            Response Code:
            "201":
                    description: Status OK. Request Successful. File uploaded to the server.
            default:
                    description: Unexpected Error.
        """
        projects = Project.objects.get(name=str(p_name))
        serializer = ProjectSerializer(projects, many=False)
        temp = serializer.data
        print(temp)
        project_name = temp['project_location']
        print(project_name)

        body = request.body.decode("utf-8")
        if not body:
            return HttpResponse(status=HTTPStatus.BAD_REQUEST)

        data = json.loads(body)
        file_contents = data['data']

        f = open(project_name, "wb")
        f.write(bytes(file_contents, 'utf-8'))
        f.close()

        return HttpResponse(HTTPStatus.OK)

