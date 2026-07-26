from django.db import models

class Testimonial(models.Model):
    name = models.CharField(max_length=200)
    role = models.CharField(max_length=200, blank=True)
    content = models.TextField()
    photo = models.ImageField(upload_to='testimonials/', blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

class GalleryImage(models.Model):
    title = models.CharField(max_length=200)
    image = models.ImageField(upload_to='gallery/', blank=True)
    category = models.CharField(max_length=100, blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.title

class DiseaseInfo(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField()
    symptoms = models.TextField(blank=True)
    prevention = models.TextField(blank=True)
    department = models.ForeignKey('departments.Department', on_delete=models.SET_NULL, null=True, blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name
