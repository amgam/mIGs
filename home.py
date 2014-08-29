#!/usr/bin/env python
#
# Copyright 2007 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
import urllib
import webapp2
import jinja2
import os
import datetime

from google.appengine.ext import blobstore
from google.appengine.ext import ndb
from google.appengine.api import users 
from google.appengine.api import mail
from google.appengine.api import images


jinja_environment = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__) + "/templates"))

# Handler for Signin page
class MainPage(webapp2.RequestHandler):
    def get(self):
        user = users.get_current_user()
        if user:  # signed in already
            parent = ndb.Key('Persons', extract(users.get_current_user().nickname()))
            person = parent.get() #checks in the db

            template_values = {
                'user_name': extract(users.get_current_user().nickname()),
                'logout': users.create_logout_url(self.request.host_url),
            }
            template = jinja_environment.get_template('Signin.html')
            self.response.out.write(template.render(template_values))
        else:
            template = jinja_environment.get_template('Signin.html')
            self.response.out.write(template.render())

class HandleOpenId(webapp2.RequestHandler):
    def get(self):
        self.redirect(self.request.host_url)

# Front page for those logged in/Main Page
class LoggedIn(webapp2.RequestHandler):
    def get(self):
        user = users.get_current_user()
        if user:  # signed in already
            parent = ndb.Key('Persons', extract(users.get_current_user().nickname()))
            person = parent.get() #checks in the db

            #need to check if person exists for first timers

            if(person is None):
                template_values = {
                'user_name': extract(users.get_current_user().nickname()),
                'logout': users.create_logout_url(self.request.host_url),
                }
                template = jinja_environment.get_template('main.html')
                self.response.out.write(template.render(template_values))
            else:
                #person exists.
                upload_url = blobstore.create_upload_url('/uploadimage')

                template_values = {
                    'user_name': person.name, 'room' : person.room, 'hp' : person.hp, 'upload_url' : upload_url,
                    'logout': users.create_logout_url(self.request.host_url),
                }

                if(person.face):
                    url = images.get_serving_url(person.face)
                    template_values['image'] = url 
                    template = jinja_environment.get_template('main.html')
                                       
                else:
                    #person exists but no face
                    template_values['image'] = "../images/profile.png"
                    template = jinja_environment.get_template('main.html')
            
            self.response.out.write(template.render(template_values))


            
        else:
            self.redirect(users.create_logout_url("/"))

class CheckUser(webapp2.RequestHandler):
    def post(self):
        currUser = ndb.Key('Persons', extract(users.get_current_user().nickname()))
        person = currUser.get()

        if person == None:
            self.response.out.write("false")
        else:
            self.response.out.write("true")

        
class InsertUser(webapp2.RequestHandler):
    def post(self):
        newUser = Persons(id = extract(users.get_current_user().nickname()))
        name = self.request.get('name')
        room = self.request.get('room')
        hp = self.request.get('hp')

        if(name and room and hp): #ensure that all fields are filled up!
            #add to db
            newUser.name = name
            newUser.room = room
            newUser.hp = hp
            newUser.put()

        self.redirect("/main")
        
class RetrieveUser(webapp2.RequestHandler):
    def post(self):
        user = users.get_current_user()

        if user:
            parent = ndb.Key('Persons', extract(users.get_current_user().nickname()))
            person = parent.get() #checks in the db

        self.response.out.write(person.name)       
            
# Datastore definitions
class Persons(ndb.Model):
    # Models a person. Key is the email.
    next_item = ndb.IntegerProperty()  # item_id for the next item
    name = ndb.StringProperty()  # name of user
    face = ndb.BlobKeyProperty() #image/face of user
    room = ndb.StringProperty()
    hp = ndb.StringProperty()
    IG = ndb.StringProperty(repeated = True)

class Feedback(ndb.Model):
    name = ndb.StringProperty()
    email = ndb.StringProperty()
    feedback = ndb.TextProperty()
    

class IG(ndb.Model):
    name = ndb.StringProperty()

class Signup(webapp2.RequestHandler):
    def post(self):
        parent = ndb.Key('Persons', extract(users.get_current_user().nickname()))
        person = parent.get() #checks in the db

        #need to check if IG is already chosen.
        #field is taken from name of page!
        new = extractIG(self.request.get('field'))

        if(new in person.IG):
            self.redirect('/old') #person is signing up twice!
            #self.response.out.write("false")
        else:
            person.IG.append(new) 
            person.put()
            

            #need to message IG head that they have a new interested member!
            #todo
            
            self.redirect("/IGlist")

# For deleting an item from wish list
class DeleteIG(webapp2.RequestHandler):
    # Delete item specified by user
    def post(self):
        person = ndb.Key('Persons', extract(users.get_current_user().nickname())).get()
        
        element = self.request.get('ig')

        if element in person.IG:
            person.IG.remove(self.request.get('ig'))
            person.put()
            
        self.redirect('/IGlist')





class GetOpenId(webapp2.RequestHandler):
    def post(self):
       openId = self.request.get('openID').rstrip()
       self.redirect(users.create_login_url('/main', None , federated_identity='https://openid.nus.edu.sg/'))


# Handler for IG page
class InterestGroup(webapp2.RequestHandler):
    # Front page for those logged in

    def get(self):
        user = users.get_current_user()
        if user:  # signed in already
            parent = ndb.Key('Persons', extract(users.get_current_user().nickname()))
            person = parent.get() #checks in the db

            template_values = {
                'user_name': person.name,
                'logout': users.create_logout_url(self.request.host_url),
            }
            template = jinja_environment.get_template('interestgroups.html')
            self.response.out.write(template.render(template_values))
        else:
            self.redirect(self.request.host_url)

# Handler for Facilities page
class Facilities(webapp2.RequestHandler):
    # Front page for those logged in

    def get(self):
        user = users.get_current_user()
        if user:  # signed in already
            parent = ndb.Key('Persons', extract(users.get_current_user().nickname()))
            person = parent.get() #checks in the db

            template_values = {
                'user_name': person.name,
                'logout': users.create_logout_url(self.request.host_url),
            }
            template = jinja_environment.get_template('facilities.html')
            self.response.out.write(template.render(template_values))
        else:
            self.redirect(self.request.host_url)

#Handler for Contact Us Page
class Contact(webapp2.RequestHandler):

    """ Form for getting and displaying contact. """

    def show(self):
        # Displays the page. Used by both get and post
        user = users.get_current_user()
        if user:  # signed in already

            # Retrieve person
            parent_key = ndb.Key('Persons', extract(users.get_current_user().nickname()))

            # Retrieve items
            query = ndb.gql("SELECT * "
                "FROM Feedback "
                "WHERE ANCESTOR IS :1 "
                ,
                parent_key)

            template_values = {
                'user_name': extract(users.get_current_user().nickname()),
                'logout': users.create_logout_url(self.request.host_url),
                'items': query,
            }

            template = jinja_environment.get_template('contact.html')
            self.response.out.write(template.render(template_values))
        else:
            self.redirect(self.request.host_url)

    def get(self):
        self.show()

    def post(self):
        # Retrieve person
        parent = ndb.Key('Persons', extract(users.get_current_user().nickname()))
        person = parent.get()

        if person == None:
            person = Persons(id=extract(users.get_current_user().nickname()))
            person.next_item = 1

        item = Feedback(parent=parent, id=str(person.next_item))
        item.item_id = person.next_item

        name = self.request.get('name')
        email = self.request.get('email')
        feedback = self.request.get('feedback')

        #for amit
        message_amit = mail.EmailMessage(sender="<dragnoth46@gmail.com>",subject="You've got feedback!",to="<dragnoth46@gmail.com>")
        message_amit.body = "Hey, you've got feedback from "+ name +"." + " Can be reached at " + email + "." + " And the user says " + feedback
        message_amit.send()

        #for tricia
        message_trish = mail.EmailMessage(sender="<dragnoth46@gmail.com>",subject="You've got feedback!",to="<tricia.tzy@gmail.com>")
        message_trish.body = "Hey, you've got feedback from "+ name +"." + " Can be reached at " + email + "." + " And the user says " + feedback
        message_trish.send()



        self.redirect("/main")

class IGadmin(webapp2.RequestHandler):
    # Front page for those logged in
    def get(self):
        user = users.get_current_user()
        if user:  # signed in already
            parent = ndb.Key('Persons', extract(users.get_current_user().nickname()))
            person = parent.get() #checks in the db

            template_values = {
                'user_name': person.name,
                'logout': users.create_logout_url(self.request.host_url),
            }
            template = jinja_environment.get_template('IGadmin.html')
            self.response.out.write(template.render(template_values))
        else:
            self.redirect(self.request.host_url)


class PerformingArts(webapp2.RequestHandler):
    # Handler for performing arts page
    def get(self):
        user = users.get_current_user()
        if user:  # signed in already
            parent = ndb.Key('Persons', extract(users.get_current_user().nickname()))
            person = parent.get() #checks in the db

            template_values = {
                'user_name': person.name,
                'logout': users.create_logout_url(self.request.host_url),
            }
            template = jinja_environment.get_template('performingarts.html')
            self.response.out.write(template.render(template_values))
        else:
            self.redirect(self.request.host_url)

class LifeStyle(webapp2.RequestHandler):
    # Handler for lifestyle arts page
    def get(self):
        user = users.get_current_user()
        if user:  # signed in already
            parent = ndb.Key('Persons', extract(users.get_current_user().nickname()))
            person = parent.get() #checks in the db

            template_values = {
                'user_name': person.name,
                'logout': users.create_logout_url(self.request.host_url),
            }
            template = jinja_environment.get_template('lifestyle.html')
            self.response.out.write(template.render(template_values))
        else:
            self.redirect(self.request.host_url)

class Sports(webapp2.RequestHandler):
    # Handler for lifestyle arts page
    def get(self):
        user = users.get_current_user()
        if user:  # signed in already
            parent = ndb.Key('Persons', extract(users.get_current_user().nickname()))
            person = parent.get() #checks in the db

            template_values = {
                'user_name': person.name,
                'logout': users.create_logout_url(self.request.host_url),
            }
            template = jinja_environment.get_template('sports.html')
            self.response.out.write(template.render(template_values))
        else:
            self.redirect(self.request.host_url)

class Culture(webapp2.RequestHandler):
    # Handler for lifestyle arts page
    def get(self):
        user = users.get_current_user()
        if user:  # signed in already
            parent = ndb.Key('Persons', extract(users.get_current_user().nickname()))
            person = parent.get() #checks in the db

            template_values = {
                'user_name': person.name,
                'logout': users.create_logout_url(self.request.host_url),
            }
            template = jinja_environment.get_template('culture.html')
            self.response.out.write(template.render(template_values))
        else:
            self.redirect(self.request.host_url)

class Specialised(webapp2.RequestHandler):
    # Handler for lifestyle arts page
    def get(self):
        user = users.get_current_user()
        if user:  # signed in already
            parent = ndb.Key('Persons', extract(users.get_current_user().nickname()))
            person = parent.get() #checks in the db

            template_values = {
                'user_name': person.name,
                'logout': users.create_logout_url(self.request.host_url),
            }
            template = jinja_environment.get_template('specialised.html')
            self.response.out.write(template.render(template_values))
        else:
            self.redirect(self.request.host_url) 

class OutReach(webapp2.RequestHandler):
    # Handler for lifestyle arts page
    def get(self):
        user = users.get_current_user()
        if user:  # signed in already
            parent = ndb.Key('Persons', extract(users.get_current_user().nickname()))
            person = parent.get() #checks in the db

            template_values = {
                'user_name': person.name,
                'logout': users.create_logout_url(self.request.host_url),
            }
            template = jinja_environment.get_template('outreach.html')
            self.response.out.write(template.render(template_values))
        else:
            self.redirect(self.request.host_url)

class Budget(webapp2.RequestHandler):
    # Handler for lifestyle arts page
    def get(self):
        user = users.get_current_user()
        if user:  # signed in already
            parent = ndb.Key('Persons', extract(users.get_current_user().nickname()))
            person = parent.get() #checks in the db

            template_values = {
                'user_name': person.name,
                'logout': users.create_logout_url(self.request.host_url),
            }
            template = jinja_environment.get_template('budget.html')
            self.response.out.write(template.render(template_values))
        else:
            self.redirect(self.request.host_url)

class Edit(webapp2.RequestHandler):
    # Handler for lifestyle arts page
    def get(self):
        user = users.get_current_user()
        if user:  # signed in already
            parent = ndb.Key('Persons', extract(users.get_current_user().nickname()))
            person = parent.get() #checks in the db

            template_values = {
                'user_name': person.name,
                'logout': users.create_logout_url(self.request.host_url),
            }
            template = jinja_environment.get_template('edit.html')
            self.response.out.write(template.render(template_values))
        else:
            self.redirect(self.request.host_url)

class trebleMakers(webapp2.RequestHandler):
    # Handler for lifestyle arts page
    def get(self):
        user = users.get_current_user()
        if user:  # signed in already
            parent = ndb.Key('Persons', extract(users.get_current_user().nickname()))
            person = parent.get() #checks in the db

            template_values = {
                'user_name': person.name,
                'logout': users.create_logout_url(self.request.host_url),
            }
            template = jinja_environment.get_template('treblemakers.html')
            self.response.out.write(template.render(template_values))
        else:
            self.redirect(self.request.host_url)

class Barefoots(webapp2.RequestHandler):
    # Handler for lifestyle arts page
    def get(self):
        user = users.get_current_user()
        if user:  # signed in already
            parent = ndb.Key('Persons', extract(users.get_current_user().nickname()))
            person = parent.get() #checks in the db

            template_values = {
                'user_name': person.name,
                'logout': users.create_logout_url(self.request.host_url),
            }
            template = jinja_environment.get_template('barefoots.html')
            self.response.out.write(template.render(template_values))
        else:
            self.redirect(self.request.host_url)

class Boltpace(webapp2.RequestHandler):
    # Handler for lifestyle arts page
    def get(self):
        user = users.get_current_user()
        if user:  # signed in already
            parent = ndb.Key('Persons', extract(users.get_current_user().nickname()))
            person = parent.get() #checks in the db

            template_values = {
                'user_name': person.name,
                'logout': users.create_logout_url(self.request.host_url),
            }
            template = jinja_environment.get_template('boltpace.html')
            self.response.out.write(template.render(template_values))
        else:
            self.redirect(self.request.host_url)

class Broadway(webapp2.RequestHandler):
    # Handler for lifestyle arts page
    def get(self):
        user = users.get_current_user()
        if user:  # signed in already
            parent = ndb.Key('Persons', extract(users.get_current_user().nickname()))
            person = parent.get() #checks in the db

            template_values = {
                'user_name': person.name,
                'logout': users.create_logout_url(self.request.host_url),
            }
            template = jinja_environment.get_template('broadway.html')
            self.response.out.write(template.render(template_values))
        else:
            self.redirect(self.request.host_url)

class DebateClub(webapp2.RequestHandler):
    # Handler for lifestyle arts page
    def get(self):
        user = users.get_current_user()
        if user:  # signed in already
            parent = ndb.Key('Persons', extract(users.get_current_user().nickname()))
            person = parent.get() #checks in the db

            template_values = {
                'user_name': person.name,
                'logout': users.create_logout_url(self.request.host_url),
            }
            template = jinja_environment.get_template('debateclub.html')
            self.response.out.write(template.render(template_values))
        else:
            self.redirect(self.request.host_url)

class DrinkingClub(webapp2.RequestHandler):
    # Handler for lifestyle arts page
    def get(self):
        user = users.get_current_user()
        if user:  # signed in already
            parent = ndb.Key('Persons', extract(users.get_current_user().nickname()))
            person = parent.get() #checks in the db

            template_values = {
                'user_name': person.name,
                'logout': users.create_logout_url(self.request.host_url),
            }
            template = jinja_environment.get_template('drinkingclub.html')
            self.response.out.write(template.render(template_values))
        else:
            self.redirect(self.request.host_url)

class Eidolon(webapp2.RequestHandler):
    # Handler for lifestyle arts page
    def get(self):
        user = users.get_current_user()
        if user:  # signed in already
            parent = ndb.Key('Persons', extract(users.get_current_user().nickname()))
            person = parent.get() #checks in the db

            template_values = {
                'user_name': person.name,
                'logout': users.create_logout_url(self.request.host_url),
            }
            template = jinja_environment.get_template('eidolonlab.html')
            self.response.out.write(template.render(template_values))
        else:
            self.redirect(self.request.host_url)

class Floorball(webapp2.RequestHandler):
    # Handler for lifestyle arts page
    def get(self):
        user = users.get_current_user()
        if user:  # signed in already
            parent = ndb.Key('Persons', extract(users.get_current_user().nickname()))
            person = parent.get() #checks in the db

            template_values = {
                'user_name': person.name,
                'logout': users.create_logout_url(self.request.host_url),
            }
            template = jinja_environment.get_template('floorball.html')
            self.response.out.write(template.render(template_values))
        else:
            self.redirect(self.request.host_url)

class Gastro(webapp2.RequestHandler):
    # Handler for lifestyle arts page
    def get(self):
        user = users.get_current_user()
        if user:  # signed in already
            parent = ndb.Key('Persons', extract(users.get_current_user().nickname()))
            person = parent.get() #checks in the db

            template_values = {
                'user_name': person.name,
                'logout': users.create_logout_url(self.request.host_url),
            }
            template = jinja_environment.get_template('gastronomy.html')
            self.response.out.write(template.render(template_values))
        else:
            self.redirect(self.request.host_url)

class Guitar(webapp2.RequestHandler):
    # Handler for lifestyle arts page
    def get(self):
        user = users.get_current_user()
        if user:  # signed in already
            parent = ndb.Key('Persons', extract(users.get_current_user().nickname()))
            person = parent.get() #checks in the db

            template_values = {
                'user_name': person.name,
                'logout': users.create_logout_url(self.request.host_url),
            }
            template = jinja_environment.get_template('guitarensemb.html')
            self.response.out.write(template.render(template_values))
        else:
            self.redirect(self.request.host_url)

class Kpop(webapp2.RequestHandler):
    # Handler for lifestyle arts page
    def get(self):
        user = users.get_current_user()
        if user:  # signed in already
            parent = ndb.Key('Persons', extract(users.get_current_user().nickname()))
            person = parent.get() #checks in the db

            template_values = {
                'user_name': person.name,
                'logout': users.create_logout_url(self.request.host_url),
            }
            template = jinja_environment.get_template('kpop.html')
            self.response.out.write(template.render(template_values))
        else:
            self.redirect(self.request.host_url)

class NightCycle(webapp2.RequestHandler):
    # Handler for lifestyle arts page
    def get(self):
        user = users.get_current_user()
        if user:  # signed in already
            parent = ndb.Key('Persons', extract(users.get_current_user().nickname()))
            person = parent.get() #checks in the db

            template_values = {
                'user_name': person.name,
                'logout': users.create_logout_url(self.request.host_url),
            }
            template = jinja_environment.get_template('nightcycling.html')
            self.response.out.write(template.render(template_values))
        else:
            self.redirect(self.request.host_url)

class Outreach(webapp2.RequestHandler):
    # Handler for lifestyle arts page
    def get(self):
        user = users.get_current_user()
        if user:  # signed in already
            parent = ndb.Key('Persons', extract(users.get_current_user().nickname()))
            person = parent.get() #checks in the db

            template_values = {
                'user_name': person.name,
                'logout': users.create_logout_url(self.request.host_url),
            }
            template = jinja_environment.get_template('outreach.html')
            self.response.out.write(template.render(template_values))
        else:
            self.redirect(self.request.host_url)

class Shuttlers(webapp2.RequestHandler):
    # Handler for lifestyle arts page
    def get(self):
        user = users.get_current_user()
        if user:  # signed in already
            parent = ndb.Key('Persons', extract(users.get_current_user().nickname()))
            person = parent.get() #checks in the db

            template_values = {
                'user_name': person.name,
                'logout': users.create_logout_url(self.request.host_url),
            }
            template = jinja_environment.get_template('shuttlers.html')
            self.response.out.write(template.render(template_values))
        else:
            self.redirect(self.request.host_url)

class Sports(webapp2.RequestHandler):
    # Handler for lifestyle arts page
    def get(self):
        user = users.get_current_user()
        if user:  # signed in already
            parent = ndb.Key('Persons', extract(users.get_current_user().nickname()))
            person = parent.get() #checks in the db

            template_values = {
                'user_name': person.name,
                'logout': users.create_logout_url(self.request.host_url),
            }
            template = jinja_environment.get_template('sports.html')
            self.response.out.write(template.render(template_values))
        else:
            self.redirect(self.request.host_url)

class tCambodia(webapp2.RequestHandler):
    # Handler for lifestyle arts page
    def get(self):
        user = users.get_current_user()
        if user:  # signed in already
            parent = ndb.Key('Persons', extract(users.get_current_user().nickname()))
            person = parent.get() #checks in the db

            template_values = {
                'user_name': person.name,
                'logout': users.create_logout_url(self.request.host_url),
            }
            template = jinja_environment.get_template('tcambodia.html')
            self.response.out.write(template.render(template_values))
        else:
            self.redirect(self.request.host_url)

class tKampung(webapp2.RequestHandler):
    # Handler for lifestyle arts page
    def get(self):
        user = users.get_current_user()
        if user:  # signed in already
            parent = ndb.Key('Persons', extract(users.get_current_user().nickname()))
            person = parent.get() #checks in the db

            template_values = {
                'user_name': person.name,
                'logout': users.create_logout_url(self.request.host_url),
            }
            template = jinja_environment.get_template('tkampung.html')
            self.response.out.write(template.render(template_values))
        else:
            self.redirect(self.request.host_url)

class TembuDoodle(webapp2.RequestHandler):
    # Handler for lifestyle arts page
    def get(self):
        user = users.get_current_user()
        if user:  # signed in already
            parent = ndb.Key('Persons', extract(users.get_current_user().nickname()))
            person = parent.get() #checks in the db

            template_values = {
                'user_name': person.name,
                'logout': users.create_logout_url(self.request.host_url),
            }
            template = jinja_environment.get_template('tembudoodle.html')
            self.response.out.write(template.render(template_values))
        else:
            self.redirect(self.request.host_url)

class tMentors(webapp2.RequestHandler):
    # Handler for lifestyle arts page
    def get(self):
        user = users.get_current_user()
        if user:  # signed in already
            parent = ndb.Key('Persons', extract(users.get_current_user().nickname()))
            person = parent.get() #checks in the db

            template_values = {
                'user_name': person.name,
                'logout': users.create_logout_url(self.request.host_url),
            }
            template = jinja_environment.get_template('tmentors.html')
            self.response.out.write(template.render(template_values))
        else:
            self.redirect(self.request.host_url)

class tStudios(webapp2.RequestHandler):
    # Handler for lifestyle arts page
    def get(self):
        user = users.get_current_user()
        if user:  # signed in already
            parent = ndb.Key('Persons', extract(users.get_current_user().nickname()))
            person = parent.get() #checks in the db

            template_values = {
                'user_name': person.name,
                'logout': users.create_logout_url(self.request.host_url),
            }
            template = jinja_environment.get_template('tstudios.html')
            self.response.out.write(template.render(template_values))
        else:
            self.redirect(self.request.host_url)

class Ukulele(webapp2.RequestHandler):
    # Handler for lifestyle arts page
    def get(self):
        user = users.get_current_user()
        if user:  # signed in already
            parent = ndb.Key('Persons', extract(users.get_current_user().nickname()))
            person = parent.get() #checks in the db

            template_values = {
                'user_name': person.name,
                'logout': users.create_logout_url(self.request.host_url),
            }
            template = jinja_environment.get_template('ukulelebeat.html')
            self.response.out.write(template.render(template_values))
        else:
            self.redirect(self.request.host_url)

class YarnGlue(webapp2.RequestHandler):
    # Handler for lifestyle arts page
    def get(self):
        user = users.get_current_user()
        if user:  # signed in already
            parent = ndb.Key('Persons', extract(users.get_current_user().nickname()))
            person = parent.get() #checks in the db

            template_values = {
                'user_name': person.name,
                'logout': users.create_logout_url(self.request.host_url),
            }
            template = jinja_environment.get_template('yarnglue.html')
            self.response.out.write(template.render(template_values))
        else:
            self.redirect(self.request.host_url)

class tKitchen(webapp2.RequestHandler):
    # Handler for lifestyle arts page
    def get(self):
        user = users.get_current_user()
        if user:  # signed in already
            parent = ndb.Key('Persons', extract(users.get_current_user().nickname()))
            person = parent.get() #checks in the db

            template_values = {
                'user_name': person.name,
                'logout': users.create_logout_url(self.request.host_url),
            }
            template = jinja_environment.get_template('tkitchen.html')
            self.response.out.write(template.render(template_values))
        else:
            self.redirect(self.request.host_url)

class Old(webapp2.RequestHandler):
    # Handler for lifestyle arts page
    def get(self):
        user = users.get_current_user()
        if user:  # signed in already
            parent = ndb.Key('Persons', extract(users.get_current_user().nickname()))
            person = parent.get() #checks in the db

            template_values = {
                'user_name': person.name,
                'logout': users.create_logout_url(self.request.host_url),
            }
            template = jinja_environment.get_template('old.html')
            self.response.out.write(template.render(template_values))
        else:
            self.redirect(self.request.host_url)

#also known on site as miGs as in my IGs
class IGlist(webapp2.RequestHandler):
    # Handler for lifestyle arts page
    def get(self):
        user = users.get_current_user()
        if user:  # signed in already
            parent = ndb.Key('Persons', extract(users.get_current_user().nickname()))
            person = parent.get() #checks in the db

            if person.IG: # list has IGs
                template_values = {
                    'user_name': person.name,
                    'logout': users.create_logout_url(self.request.host_url),
                    'List' : person.IG,
                }
                template = jinja_environment.get_template('IGlist.html')
                self.response.out.write(template.render(template_values))
                
            else: #no IGs, suggest user to register for IGs
                self.redirect('/noIG')
                
        else:
            self.redirect(self.request.host_url)

class noIG(webapp2.RequestHandler):
    # Handler for lifestyle arts page
    def get(self):
        user = users.get_current_user()
        if user:  # signed in already
            parent = ndb.Key('Persons', extract(users.get_current_user().nickname()))
            person = parent.get() #checks in the db

            template_values = {
                'user_name': person.name,
                'logout': users.create_logout_url(self.request.host_url),
            }
            template = jinja_environment.get_template('noIG.html')
            self.response.out.write(template.render(template_values))
        else:
            self.redirect(self.request.host_url)

class Profile(webapp2.RequestHandler):
    # Handler for lifestyle arts page
    def get(self):
        user = users.get_current_user()
        if user:  # signed in already
            parent = ndb.Key('Persons', extract(users.get_current_user().nickname()))
            person = parent.get() #checks in the db

            upload_url = blobstore.create_upload_url('/uploadimage')

            if(person.face):
                url = images.get_serving_url(person.face)
                template = jinja_environment.get_template('profile.html')

                template_values = {
                'user_name': person.name, 'room' : person.room, 'hp' : person.hp, 'image' : url, 'upload_url' : upload_url,
                'logout': users.create_logout_url(self.request.host_url),
                }
            else:
                template_values = {
                    'user_name': person.name, 'room' : person.room, 'hp' : person.hp, 'upload_url' : upload_url,
                    'logout': users.create_logout_url(self.request.host_url),
                }
                template = jinja_environment.get_template('profileblank.html')
            
            self.response.out.write(template.render(template_values))
        else:
            self.redirect(self.request.host_url)

from google.appengine.ext.webapp import blobstore_handlers

class UploadImage(blobstore_handlers.BlobstoreUploadHandler):
    def post(self):
        upload_files = self.get_uploads('file')
        blob_info = upload_files[0]

        parent = ndb.Key('Persons', extract(users.get_current_user().nickname()))
        person = parent.get() #checks in the db

        person.face = blob_info.key()
        person.put()

        self.redirect('/profile') 
    
class tCrew(webapp2.RequestHandler):
    # Handler for lifestyle arts page
    def get(self):
        user = users.get_current_user()
        if user:  # signed in already
            parent = ndb.Key('Persons', extract(users.get_current_user().nickname()))
            person = parent.get() #checks in the db

            template_values = {
                'user_name': person.name,
                'logout': users.create_logout_url(self.request.host_url),
            }
            template = jinja_environment.get_template('tcrew.html')
            self.response.out.write(template.render(template_values))
        else:
            self.redirect(self.request.host_url)

class Offtrek(webapp2.RequestHandler):
    # Front page for those logged in

    def get(self):
        user = users.get_current_user()
        if user:  # signed in already
            parent = ndb.Key('Persons', extract(users.get_current_user().nickname()))
            person = parent.get() #checks in the db

            template_values = {
                'user_name': person.name,
                'logout': users.create_logout_url(self.request.host_url),
            }
            template = jinja_environment.get_template('offtrek.html')
            self.response.out.write(template.render(template_values))
        else:
            self.redirect(self.request.host_url)

class TableTops(webapp2.RequestHandler):
    # Front page for those logged in

    def get(self):
        user = users.get_current_user()
        if user:  # signed in already
            parent = ndb.Key('Persons', extract(users.get_current_user().nickname()))
            person = parent.get() #checks in the db

            template_values = {
                'user_name': person.name,
                'logout': users.create_logout_url(self.request.host_url),
            }
            template = jinja_environment.get_template('tabletops.html')
            self.response.out.write(template.render(template_values))
        else:
            self.redirect(self.request.host_url)

class TableTennis(webapp2.RequestHandler):
    # Front page for those logged in

    def get(self):
        user = users.get_current_user()
        if user:  # signed in already
            parent = ndb.Key('Persons', extract(users.get_current_user().nickname()))
            person = parent.get() #checks in the db

            template_values = {
                'user_name': person.name,
                'logout': users.create_logout_url(self.request.host_url),
            }
            template = jinja_environment.get_template('tabletennis.html')
            self.response.out.write(template.render(template_values))
        else:
            self.redirect(self.request.host_url)

class Captain(webapp2.RequestHandler):
    # Front page for those logged in

    def get(self):
        user = users.get_current_user()
        if user:  # signed in already
            parent = ndb.Key('Persons', extract(users.get_current_user().nickname()))
            person = parent.get() #checks in the db

            template_values = {
                'user_name': person.name,
                'logout': users.create_logout_url(self.request.host_url),
            }
            template = jinja_environment.get_template('captainsball.html')
            self.response.out.write(template.render(template_values))
        else:
            self.redirect(self.request.host_url)

class SkateBoard(webapp2.RequestHandler):
    # Front page for those logged in

    def get(self):
        user = users.get_current_user()
        if user:  # signed in already
            parent = ndb.Key('Persons', extract(users.get_current_user().nickname()))
            person = parent.get() #checks in the db

            template_values = {
                'user_name': person.name,
                'logout': users.create_logout_url(self.request.host_url),
            }
            template = jinja_environment.get_template('skateboard.html')
            self.response.out.write(template.render(template_values))
        else:
            self.redirect(self.request.host_url)

class StarGazers(webapp2.RequestHandler):
    # Front page for those logged in

    def get(self):
        user = users.get_current_user()
        if user:  # signed in already
            parent = ndb.Key('Persons', extract(users.get_current_user().nickname()))
            person = parent.get() #checks in the db

            template_values = {
                'user_name': person.name,
                'logout': users.create_logout_url(self.request.host_url),
            }
            template = jinja_environment.get_template('stargazers.html')
            self.response.out.write(template.render(template_values))
        else:
            self.redirect(self.request.host_url)

class Stretch(webapp2.RequestHandler):
    # Front page for those logged in

    def get(self):
        user = users.get_current_user()
        if user:  # signed in already
            parent = ndb.Key('Persons', extract(users.get_current_user().nickname()))
            person = parent.get() #checks in the db

            template_values = {
                'user_name': person.name,
                'logout': users.create_logout_url(self.request.host_url),
            }
            template = jinja_environment.get_template('stretchtone.html')
            self.response.out.write(template.render(template_values))
        else:
            self.redirect(self.request.host_url)

class Football(webapp2.RequestHandler):
    # Front page for those logged in

    def get(self):
        user = users.get_current_user()
        if user:  # signed in already
            parent = ndb.Key('Persons', extract(users.get_current_user().nickname()))
            person = parent.get() #checks in the db

            template_values = {
                'user_name': person.name,
                'logout': users.create_logout_url(self.request.host_url),
            }
            template = jinja_environment.get_template('football.html')
            self.response.out.write(template.render(template_values))
        else:
            self.redirect(self.request.host_url)

#function to extract matric number
def extract(st):
    return st[26:34]

def extractIG(st):
    arr = st.split() #contains arr of single words
    #concate till | is found
    final = helper(arr, "")
    return final

def helper(arr, st):
    if (arr[0] == "|"):
        return st
    else:
        if st == "":
            st = st + arr[0]
        else:
            st = st + " " + arr[0] # concate word

        return helper(arr[1:], st)

app = webapp2.WSGIApplication([('/', MainPage), ('/main', LoggedIn),('/contact', Contact),('/IGadmin', IGadmin), ('/performingarts', PerformingArts),
     ('/getOpenId', GetOpenId), ('/_ah/login_required', HandleOpenId), ('/interestgroups', InterestGroup),('/facilities', Facilities),('/lifestyle', LifeStyle),
     ('/sports', Sports), ('/culture', Culture), ('/specialised', Specialised), ('/outreach', OutReach), ('/budget', Budget), ('/edit', Edit), ('/treblemakers', trebleMakers), ('/checkuser', CheckUser)
     ,('/insertuser', InsertUser),('/retrieveuser', RetrieveUser),('/signup', Signup),('/barefoots', Barefoots),('/boltpace', Boltpace),('/broadway', Broadway),('/debateclub', DebateClub),('/drinkingclub', DrinkingClub)
     ,('/eidolonlab', Eidolon),('/floorball', Floorball),('/gastronomy', Gastro),('/guitarensemb', Guitar),('/kpop', Kpop),('/nightcycling', NightCycle)
     ,('/outreach', Outreach),('/shuttlers', Shuttlers),('/sports', Sports),('/tcambodia', tCambodia),('/tembudoodle', TembuDoodle),('/tkampung', tKampung)
     ,('/tmentors', tMentors),('/tstudios', tStudios),('/ukulelebeat', Ukulele),('/yarnglue', YarnGlue),('/tkitchen', tKitchen),('/old', Old)
     ,('/IGlist', IGlist),('/deleteig', DeleteIG),('/noIG', noIG),('/profile', Profile),('/uploadimage', UploadImage),('/tcrew', tCrew),('/offtrek', Offtrek)
     ,('/tabletops', TableTops),('/tabletennis', TableTennis),('/captainsball', Captain),('/skateboard', SkateBoard),('/stargazers', StarGazers)
     ,('/football', Football)]
     ,debug=True)

