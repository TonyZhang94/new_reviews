from django.db import models
from django.utils import timezone

# Create your models here.


class Task_state(models.Model):
	STATUSES = (
		(1, 'not started'),
		(2, 'processing'),
		(3, 'finished'),
	)

	pcid = models.CharField(max_length=5)
	cid = models.CharField(max_length=20)
	lastfinishedtime = models.DateTimeField(null=True)
	step_1_status = models.CharField(max_length=10)
	step_1_time = models.DateTimeField(null=True)
	step_2_status = models.CharField(max_length=10)
	step_2_time = models.DateTimeField(null=True)
	step_3_status = models.CharField(max_length=10)
	step_3_time = models.DateTimeField(null=True)
	step_4_status = models.CharField(max_length=10)
	step_4_time = models.DateTimeField(null=True)
	step_2_clutser_status = models.IntegerField(default = 0)
	step_2_cluster_alpha = models.FloatField(default = 0.85)
	step_2_feature_limit = models.IntegerField(default = 10)
	status = models.IntegerField(choices=STATUSES, verbose_name='任务状态', default=1)
