from django import forms
from django.core.exceptions import ValidationError
from tinymce.widgets import TinyMCE
from .models import BlogPost, Comment
import re


class BlogPostAdminForm(forms.ModelForm):
    content = forms.CharField(
        widget=TinyMCE(
            attrs={
                'cols': 300,     
                'rows': 40
            }
        )
    )

    class Meta:
        model = BlogPost
        fields = "__all__"


class CommentForm(forms.ModelForm):
    """
    Form for anonymous visitor comments with validation.
    
    Validates:
    - first_name: Required, letters/spaces/hyphens/apostrophes only
    - last_name: Required, letters/spaces/hyphens/apostrophes only
    - content: Required, max 2000 characters
    """
    
    class Meta:
        model = Comment
        fields = ['first_name', 'last_name', 'content']
    
    def clean_first_name(self):
        """
        Validate first_name field.
        
        Requirements:
        - Not empty after stripping whitespace
        - Contains only letters, spaces, hyphens, and apostrophes
        
        Returns:
            str: Cleaned first name
        
        Raises:
            ValidationError: If validation fails
        """
        name = self.cleaned_data['first_name'].strip()
        
        if not name:
            raise ValidationError("First name is required")
        
        # Allow letters (any language), spaces, hyphens, and apostrophes
        if not re.match(r'^[a-zA-Z\s\-\']+$', name):
            raise ValidationError("First name contains invalid characters. Only letters, spaces, hyphens, and apostrophes are allowed.")
        
        return name
    
    def clean_last_name(self):
        """
        Validate last_name field.
        
        Requirements:
        - Not empty after stripping whitespace
        - Contains only letters, spaces, hyphens, and apostrophes
        
        Returns:
            str: Cleaned last name
        
        Raises:
            ValidationError: If validation fails
        """
        name = self.cleaned_data['last_name'].strip()
        
        if not name:
            raise ValidationError("Last name is required")
        
        # Allow letters (any language), spaces, hyphens, and apostrophes
        if not re.match(r'^[a-zA-Z\s\-\']+$', name):
            raise ValidationError("Last name contains invalid characters. Only letters, spaces, hyphens, and apostrophes are allowed.")
        
        return name
    
    def clean_content(self):
        """
        Validate content field.
        
        Requirements:
        - Not empty after stripping whitespace
        - Max 2000 characters
        
        Returns:
            str: Cleaned content
        
        Raises:
            ValidationError: If validation fails
        """
        content = self.cleaned_data['content'].strip()
        
        if not content:
            raise ValidationError("Comment content is required")
        
        if len(content) > 2000:
            raise ValidationError("Comment is too long (max 2000 characters)")
        
        return content