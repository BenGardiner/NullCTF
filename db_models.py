import os
import logging

from pymodm import MongoModel, EmbeddedMongoModel, fields, connect
import config_vars

connect(config_vars.mongodb_connection)

# class BotConfig(object):
#     ANNOUNCEMENTS_CHANNEL = fields.IntegerField()
#     REMINDERS_CHANNEL = fields.IntegerField()


# class InstalledCogs(MongoModel):
#     name = fields.CharField(required=True)
#     enabled = fields.BooleanField(default=True)


class Challenge(EmbeddedMongoModel):
    name = fields.CharField(required=True)
    created_at = fields.DateTimeField(required=True)
    tags = fields.ListField(fields.CharField(), default=[], blank=True)
    attempted_by = fields.ListField(fields.CharField(), default=[])
    solved_at = fields.DateTimeField(blank=True)
    solved_by = fields.ListField(fields.CharField(), default=[], blank=True)
    notebook_url = fields.CharField(default="", blank=True)
    flag = fields.CharField()


class CTFModel(MongoModel):
    name = fields.CharField(required=True)
    category_id = fields.IntegerField()
    role_id = fields.IntegerField()
    description = fields.CharField()
    created_at = fields.DateTimeField(required=True)
    finished_at = fields.DateTimeField()
    start_date = fields.DateTimeField()
    end_date = fields.DateTimeField()
    url = fields.URLField()
    username = fields.CharField()
    password = fields.CharField()
    challenges = fields.EmbeddedDocumentListField(Challenge, default=[], blank=True)
    pending_reminders = fields.ListField(blank=True, default=[])

    def status(self, members_joined_count):

        description_str = self.description + "\n" if self.description else ""

        solved_count = len(
            list(filter(lambda x: x.solved_at is not None, self.challenges))
        )
        total_count = len(self.challenges)
        status = (
            f":triangular_flag_on_post: **{self.name}** ({members_joined_count} Members joined)\n{description_str}"
            # + f"```CSS\n{draw_bar(solved_count, total_count, style=5)}\n"
            + f" {solved_count} Solved / {total_count} Total"
        )
        if self.start_date:
            fmt_str = "%d/%m %H:\u200b%M"
            start_date_str = self.start_date.strftime(fmt_str)
            end_date_str = self.end_date.strftime(fmt_str) if self.end_date else "?"
            status += f"\n {start_date_str} - {end_date_str}\n"
        status += "```"
        return status

    def credentials(self):
        response = f":busts_in_silhouette: **Username**: {self.username}\n:key: **Password**: {self.password}"
        if self.url is not None:
            response += f"\n\nLogin Here: {self.url}"
        return response
    
    def get_challenge(self, name):
        return next((c for c in self.challenges if c.name == name), None)

    def challenge_summary(self):
        if not self.challenges:
            return "No challenges found. Adding one with `>challenge add <name> <category>`"

        solved_response, unsolved_response = "", ""

        for challenge in sorted(self.challenges, key=lambda c: c.solved_at or c.created_at):
            challenge_details = f'**[{challenge.name}]**'
            if challenge.solved_at:
                solved_response += f'{challenge_details} solved by: {", ".join(challenge.solved_by)}\n'
            else:
                unsolved_response += f'{challenge_details} attempted by: {", ".join(challenge.attempted_by)}\n'
        
        summary = (
            f"\\>>> Solved :white_check_mark: \n{solved_response}" + f"\\>>> Unsolved :thinking:\n{unsolved_response}"
        )
        return summary

    class Meta:
        collection_name = "ctf"
        ignore_unknown_fields = True