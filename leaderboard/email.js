const nodemailer = require('nodemailer');

function createTransporter() {
  const host = process.env.SMTP_HOST;
  const user = process.env.SMTP_USER;
  const pass = process.env.SMTP_PASS;

  if (!host || !user || !pass) {
    return null;
  }

  return nodemailer.createTransport({
    host,
    port: parseInt(process.env.SMTP_PORT || '587', 10),
    secure: false,
    auth: { user, pass },
  });
}

function formatTime(hours, minutes, seconds) {
  return `${String(hours).padStart(2, '0')}:${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;
}

async function sendApprovalEmail(submission) {
  const transporter = createTransporter();
  if (!transporter) {
    console.log(`[Email] SMTP not configured. Would send approval email to ${submission.email}`);
    return;
  }

  const time = formatTime(submission.hours, submission.minutes, submission.seconds);

  await transporter.sendMail({
    from: process.env.EMAIL_FROM || 'noreply@threepeaks.com',
    to: submission.email,
    subject: 'Three Peaks Challenge - Submission Approved!',
    html: `
      <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <div style="background: linear-gradient(135deg, #1a5276, #2e86c1); padding: 30px; text-align: center; border-radius: 8px 8px 0 0;">
          <h1 style="color: white; margin: 0;">Three Peaks Challenge</h1>
        </div>
        <div style="padding: 30px; background: #f8f9fa; border-radius: 0 0 8px 8px;">
          <h2 style="color: #1a5276;">Congratulations, ${submission.name}!</h2>
          <p>Your Three Peaks Challenge submission has been approved and is now live on our leaderboard.</p>
          <div style="background: white; padding: 20px; border-radius: 8px; border-left: 4px solid #2e86c1; margin: 20px 0;">
            <p style="margin: 0;"><strong>Your Time:</strong> ${time}</p>
          </div>
          <p>Check out the leaderboard to see where you rank!</p>
          <p style="color: #666; font-size: 14px; margin-top: 30px;">Keep challenging yourself!</p>
        </div>
      </div>
    `,
  });

  console.log(`[Email] Approval email sent to ${submission.email}`);
}

module.exports = { sendApprovalEmail };
