from rest_framework import serializers
from .models import Project, Connector, Machine, Simulation

class ProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        #fields = ('name', 'host_machine', 'status')
        fields = '__all__'

class ConnectorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Connector
        fields = '__all__'

class MachineSerializer(serializers.ModelSerializer):
    class Meta:
        model = Machine
        fields = '__all__'

class SimulationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Simulation
        fields = '__all__'
