from reformatter import *
import logging
import logging.handlers


# load parameters from environment secrets
email_username = set_from_env('EMAIL_USERNAME', 'vital')
email_password = set_from_env('EMAIL_PASSWORD', 'vital')
email_recipients_cs = set_from_env('EMAIL_RECIPIENTS_CS', 'vital')
email_recipients_physics = set_from_env('EMAIL_RECIPIENTS_PHYSICS', email_recipients_cs)
email_recipients_all = []  # generate unique list of recipients from all categories
email_recipients_all = [x for x in email_recipients_cs + email_recipients_physics if x not in email_recipients_all and
                        not email_recipients_all.append(x)]
trash_fetched = set_from_env('TRASH_FETCHED', True)
mark_cs = set_from_env('MARK_CS', None)
mark_physics = set_from_env('MARK_PHYSICS', mark_cs)
advertise_marked = set_from_env('ADVERTISE_MARKED', True)
skip_cs = set_from_env('SKIP_CS', None)
skip_physics = set_from_env('SKIP_PHYSICS', skip_cs)

# set logger instance
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger_file_handler = logging.handlers.RotatingFileHandler(
    "status.log",
    maxBytes=1024 * 1024,
    backupCount=1,
    encoding="utf8",
)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger_file_handler.setFormatter(formatter)
logger.addHandler(logger_file_handler)

if __name__ == "__main__":
    # initialize the reformatter
    reformatter = ArxivReformatter(email_username, email_password, trash_fetched)

    # loop over emails
    from_arxiv = ['first iteration']
    while from_arxiv:
        # fetch first email
        from_arxiv, cur_msg, date_time = reformatter.fetch_emails(from_arxiv)
        title = extract_email_category(cur_msg)
        msg_id = from_arxiv.pop(0)

        # reformat email
        if title == 'physics':
            html_msg, is_marked = reformat_email(msg=cur_msg, ttl=title, mark_authors=mark_physics,
                                                 skip_words=skip_physics)
            email_recipients = email_recipients_physics
        else:
            html_msg, is_marked = reformat_email(msg=cur_msg, ttl=title, mark_authors=mark_cs, skip_words=skip_cs)
            email_recipients = email_recipients_cs

        if is_marked and advertise_marked:
            email_recipients = email_recipients_physics + email_recipients_cs

        # send email
        email_subject = title + " arXiv, " + date_time[5:16]
        reformatter.send_email(msg=html_msg, subject=email_subject, recipients=email_recipients)

        # delete the original message from the server:
        if trash_fetched:
            reformatter.mail_imap.store(msg_id, '+X-GM-LABELS', '\\Trash')

        # log the message
        logger.info(f"Fetched email from: {date_time}")

    # close the connection and logout
    reformatter.close_connection()
