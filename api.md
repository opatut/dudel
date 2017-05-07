```
x GET    /status

x POST   /users           # Register
x PUT    /users/<id>      # Edit profile / settings
x GET    /users/<id>
x GET    /users/me        # Currently logged in user

  POST   /polls
  GET    /polls/<id|slug>
  PUT    /polls/<id|slug>
  DELETE /polls/<id|slug>
  GET    /polls/<id|slug>/choices
  POST   /polls/<id|slug>/choices
  PUT    /polls/<id|slug>/choices/<id>
  DELETE /polls/<id|slug>/choices/<id>
  GET    /polls/<id|slug>/values
  POST   /polls/<id|slug>/values
  PUT    /polls/<id|slug>/values/<id>
  DELETE /polls/<id|slug>/values/<id>
  GET    /polls/<id|slug>/votes
  POST   /polls/<id|slug>/votes
  PUT    /polls/<id|slug>/votes/<id>
  DELETE /polls/<id|slug>/votes/<id>

  GET    /polls/<id|slug>/comments
  POST   /polls/<id|slug>/comments
  DELETE /polls/<id|slug>/comments/<id>

  PUT    /polls/<id|slug>/watch
  DELETE /polls/<id|slug>/watch

  GET    /groups
  POST   /groups
  PUT    /groups/<id>
  GET    /groups/<id>
  DELETE /groups/<id>
  GET    /groups/<id>/members
  PUT    /groups/<id>/members/<user_id>
  DELETE /groups/<id>/members/<user_id>

  GET    /polls/<id|slug>/invitations
  POST   /polls/<id|slug>/invitations
  DELETE /polls/<id|slug>/invitations/<id>
  GET    /invitations
  GET    /invitations/<id>
  PUT    /invitations/<id>

  GET    /stats
```

## Notes

* User polls

  - watching
  - owned 
  - owned by groups 
  - voted on
  - invited to
