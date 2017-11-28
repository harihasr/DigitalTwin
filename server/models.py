# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.db import models
from django_mysql.models import ListCharField
import uuid

# Create your models here.


# Database models
class Project(models.Model):
    name = models.CharField(max_length=40)
    # host_machine = models.URLField()
    # status_bool = models.BooleanField(default=False)
    # status = models.CharField(max_length=10)
    project_location = models.CharField(max_length=200)

    def __str__(self):
        return "%s %s" % (self.name, self.project_location)


class Machine(models.Model):
    name = models.CharField(max_length=150, unique=True)
    address = models.CharField(max_length=150, unique=True)
    agent_port = models.IntegerField()

    def __str__(self):
        return "{} {} {}".format(self.name, self.address, self.agent_port)


class Simulation(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.CharField(max_length=40, null=True)
    machine = models.CharField(max_length=150, null=True)

    def __str__(self):
        return "%d %s %s" % (self.id, self.project, self.machine)


class Connector(models.Model):
    name = models.CharField(max_length=25, null=True)
    ts = models.CharField(max_length=25, null=True)
    sync_to_rt = models.CharField(max_length=25, null=True)
    ip_address = models.CharField(max_length=25, null=True)
    host_name = models.CharField(max_length=40, null=True)
    port = models.CharField(max_length=25, null=True)
    conn_timeout = models.CharField(max_length=25, null=True)
    io_timeout = models.CharField(max_length=25, null=True)
    from_simulation = ListCharField(base_field=models.CharField(max_length = 20, null=True), size=10,
                                    max_length=(25*10), null=True)
    to_simulation = ListCharField(base_field=models.CharField(max_length = 20, null=True), size=10,
                                  max_length = (25*10), null=True)
    project = models.ForeignKey(Project, on_delete=models.CASCADE)

    def __str__(self):
        return "%s %s %s %s %s %s %s %s %s" % (self.name, self.ts, self.sync_to_rt, self.ip_address,
                                               self.host_name, self.port, self.conn_timeout, self.from_simulation,
                                               self.to_simulation)
